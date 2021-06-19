using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;
using Client.FileWatcherLibrary;

namespace Client
{
    class Program
    {
        private static readonly IPAddress ServerIp = IPAddress.Loopback;
        private const int ServerPort = 1337;
        private static readonly byte[] EndCode = Encoding.UTF8.GetBytes("\r\n\r\n").ToArray();

        private static readonly Socket Server = new Socket(AddressFamily.InterNetwork, SocketType.Stream,
            ProtocolType.Tcp);

        private static string _userName;

        private static FileWatcher _watcher;
        private static string _directoryPath;
        private static string _zipPath;

        static void Main(string[] args)
        {
            Server.Connect(IPAddress.Loopback, ServerPort);
            SendMessage("HI\r\n\r\n", Server); //HI\r\n\r\n
            string message = ReceiveDataInString(Server, EndCode);
            int messageCode = GetMessageCode(message); //101 HI\r\n\r\n
            if (messageCode != 100)
                return;
            while (true)
            {
                Console.WriteLine("Podaj login");
                _userName = Console.ReadLine();
                Console.WriteLine("Podaj hasło");
                var password = Console.ReadLine();

                if (string.IsNullOrEmpty(_userName) || string.IsNullOrEmpty(password))
                {
                    continue;
                }

                SendMessage($"LOGIN\r\n{_userName}\r\n{password}\r\n\r\n",
                    Server); //LOGIN\r\nUSERNAME\r\nPASSWORD\r\n\r\n

                message = ReceiveDataInString(Server, EndCode);
                messageCode = GetMessageCode(message);
                if (messageCode == 403) //404 BAD PASSWORD\r\n\r\n
                {
                    continue;
                }

                if (messageCode == 240) //240 LOGGED IN SESIONID = __SESIONID__\r\n\r\n
                {
                    break;
                }
            }

            if (args.Length == 0)
            {
                _directoryPath = @"C:\synchronizacjaKlient\rider\" + _userName;
                _zipPath = @"C:\synchronizacjaKlient\rider\" + _userName + ".zip";
            }
            else
            {
                _directoryPath = @"C:\synchronizacjaKlient" + @"\" + args[0] + @"\" + _userName;
                _zipPath = @"C:\synchronizacjaKlient" + @"\" + args[0] + @"\" + _userName + ".zip";
            }


            Console.WriteLine(_directoryPath);
            message = ReceiveDataInString(Server, EndCode); //260 __PORT__ __ROZMIAR_PLIKU__
            messageCode = GetMessageCode(message);
            if (messageCode != 260)
            {
                return;
            }

            int port = int.Parse(message.Split().ElementAt(2));
            int directoryInZipLength = int.Parse(message.Split().ElementAt(3));
            var directoryInZip = DownloadFile(directoryInZipLength, ServerIp, port);

            if (File.Exists(_zipPath))
            {
                File.Delete(_zipPath);
            }

            File.WriteAllBytes(_zipPath, directoryInZip.ToArray());

            if (Directory.Exists(_directoryPath))
            {
                Directory.Delete(_directoryPath, true);
            }

            ZipFile.ExtractToDirectory(_zipPath, _directoryPath);

            if (!Directory.Exists(_directoryPath))
            {
                Directory.CreateDirectory(_directoryPath);
            }

            _watcher = new FileWatcher(_directoryPath, TimeSpan.FromSeconds(5));
            _watcher.StartWatching();
            _watcher.FilesModified += OnFilesModified;
            WaitForServerRequest(Server);
        }

        private static void WaitForServerRequest(Socket socket)
        {
            while (true)
            {
                var message = ReceiveDataInString(socket, EndCode);
                var messageCode = int.Parse(message.Split().First());
                if (messageCode == 260) //267 CHANGE __PORT__ __ROZMIAR__
                {
                    _watcher.StopWatching();
                    int port = int.Parse(message.Split().ElementAt(2));
                    int directoryInZipLength = int.Parse(message.Split().ElementAt(3));
                    Console.WriteLine($"PORT: {port} Długość: {directoryInZipLength}");
                    var directoryInZip = DownloadFile(directoryInZipLength, ServerIp, port);
                    if (File.Exists(_zipPath))
                    {
                        File.Delete(_zipPath);
                    }

                    File.WriteAllBytes(_zipPath, directoryInZip.ToArray());
                    if (Directory.Exists(_directoryPath))
                    {
                        Directory.Delete(_directoryPath, true);
                    }

                    ZipFile.ExtractToDirectory(_zipPath, _directoryPath);
                    if (!Directory.Exists(_directoryPath))
                    {
                        Directory.CreateDirectory(_directoryPath);
                    }

                    _watcher.StartWatching();
                }
            }
        }

        static int GetMessageCode(string message)
        {
            var codeInString = message.Split().First();
            return int.Parse(codeInString);
        }

        private static List<byte> DownloadFile(int fileSize, IPAddress ip, int port)
        {
            var downloadSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            downloadSocket.Connect(ip, port);
            SendMessage("READY\r\n\r\n", downloadSocket); //READY\r\n\r\n            

            List<byte> result = new List<byte>();
            byte[] buffer = new Byte[1];

            for (int i = 0; i < fileSize; i++)
            {
                downloadSocket.Receive(buffer, 1, SocketFlags.None); //Przesyłanie zipa na nowym porcie
                result.Add(buffer[0]);
            }

            SendMessage("SUCCESS\r\n\r\n", downloadSocket); //SUCCESS\r\n\r\n
            return result;
        }

        static void SendMessage(string message, Socket socket)
        {
            Console.WriteLine("Wysłano wiadomość" + message);
            socket.Send(Encoding.UTF8.GetBytes(message));
        }

        static string ReceiveDataInString(Socket socket, byte[] endCode)
        {
            List<byte> receiveDataInBytes = ReceiveDataInBytes(socket, endCode);
            var dataInString = Encoding.UTF8.GetString(receiveDataInBytes.ToArray());
            Console.WriteLine("Odebrano wiadomość" + dataInString);
            return dataInString;
        }

        static List<byte> ReceiveDataInBytes(Socket socket, byte[] endCode)
        {
            List<byte> result = new List<byte>();
            byte[] buffer = new Byte[1];
            do
            {
                socket.Receive(buffer, 1, SocketFlags.None);
                result.Add(buffer[0]);
            } while (!IsEndCodeReceived(result, endCode));

            return result.GetRange(0, result.Count - endCode.ToList().Count);
        }

        private static bool IsEndCodeReceived(List<byte> message, byte[] endCode)
        {
            var endCodeInList = endCode.ToList();
            return (endCodeInList.Count <= message.Count) &&
                   endCodeInList.SequenceEqual(message.GetRange(message.Count - endCodeInList.Count,
                       endCodeInList.Count));
        }

        private static void OnFilesModified(IEnumerable<ModifiedFile> modifiedFiles)
        {
            Console.WriteLine("OnFilesModified");
            foreach (var modifiedFile in modifiedFiles)
            {
                Console.WriteLine(
                    $"{DateTime.Now} {modifiedFile.FilePath}: {modifiedFile.ModificationType.ToString()}");
            }

            Task.Run(SendDirectory);
        }

        private static void SendDirectory()
        {
            _watcher.StopWatching();
            File.Delete(_zipPath);
            ZipFile.CreateFromDirectory(_directoryPath, _zipPath);
            var zipLength = new FileInfo(_zipPath).Length;
            int randPort = new Random().Next(10000, 65535);

            var sendFileSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            var sendFileEndPoint = new IPEndPoint(ServerIp, randPort);

            sendFileSocket.Bind(sendFileEndPoint);
            sendFileSocket.Listen(1);
            SendMessage($"CHANGE\r\n{randPort}\r\n{zipLength}\r\n\r\n",
                Server); //CHANGE __SESIONID__ __PORT__  __ROZMIAR__
            var sendFileClient = sendFileSocket.Accept();
            var message = ReceiveDataInString(sendFileClient, EndCode);
            if (message != "READY") //READY\r\n\r\n
            {
                return;
            }

            sendFileClient.SendFile(_zipPath); //Przesyłanie zipa na nowym porcie

            message = ReceiveDataInString(sendFileClient, EndCode);
            if (message == "SUCCESS") //SUCCESS\r\n\r\n
            {
            }

            sendFileClient.Close();
            _watcher.StartWatching();
        }
    }
}