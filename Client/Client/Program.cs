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
        private static string _sessionId;

        static void Main(string[] args)
        {
            Server.Connect(IPAddress.Loopback, ServerPort);
            SendMessage("HI\r\n", Server);                                                                              //HI\r\n\r\n
            string message = ReceiveDataInString(Server, EndCode);
            int messageCode = GetMessageCode(message);                                                                  //101 HI\r\n\r\n
            Console.WriteLine(message);
            if (messageCode != 101)
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
                    Server);                                                                                            //LOGIN\r\nUSERNAME\r\nPASSWORD\r\n\r\n

                message = ReceiveDataInString(Server, EndCode);
                messageCode = GetMessageCode(message);
                if (messageCode == 404)                                                                                 //404 BAD PASSWORD\r\n\r\n
                {
                    continue;
                }

                if (messageCode == 240)                                                                                 //240 LOGGED IN SESIONID = __SESIONID__\r\n\r\n
                {
                    _sessionId = message.Split().Last();
                    break;
                }
            }

            message = ReceiveDataInString(Server, EndCode);                                                             //241 __PORT__ __ROZMIAR_PLIKU__
            messageCode = GetMessageCode(message);
            if (messageCode != 241)
            {
                return;
            }

            int port = int.Parse(message.Split().ElementAt(1));
            int directoryInZipLength = int.Parse(message.Split().ElementAt(2));
            var directoryInZip = DownloadFile(directoryInZipLength, ServerIp, port);

            File.WriteAllBytes($"{_userName}.zip", directoryInZip.ToArray());
            ZipFile.ExtractToDirectory($"{_userName}.zip", _userName);

            Task.Run(() => WaitForFileChanged(Server, _userName));

            WaitForServerRequest(Server);
        }

        private static void WaitForServerRequest(Socket socket)
        {
            while (true)
            {
                var message = ReceiveDataInString(socket, EndCode);
                Console.WriteLine(message);
                var messageCode = int.Parse(message.Split().First());
                if (messageCode == 267)                                                                                 //267 CHANGE __PORT__ __ROZMIAR__
                {
                    int port = int.Parse(message.Split().ElementAt(1));
                    int directoryInZipLength = int.Parse(message.Split().ElementAt(2));
                    var directoryInZip = DownloadFile(directoryInZipLength, ServerIp, port);
                    File.WriteAllBytes($"{_userName}.zip", directoryInZip.ToArray());
                    ZipFile.ExtractToDirectory($"{_userName}.zip", _userName);
                }
            }
        }

        static int GetMessageCode(string message)
        {
            return int.Parse(message.Split().First());
        }

        private static void WaitForFileChanged(Socket socket, string directoryPath)
        {
            using var watcher = new FileWatcher(directoryPath, TimeSpan.FromSeconds(5));
            watcher.StartWatching();
            watcher.FilesModified += OnFilesModified;
        }

        private static List<byte> DownloadFile(int fileSize, IPAddress ip, int port)
        {
            var downloadSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            downloadSocket.Connect(ip, port);
            SendMessage("READY\r\n\r\n", downloadSocket);                                                               //READY\r\n\r\n            

            List<byte> result = new List<byte>();
            byte[] buffer = new Byte[1];

            for (int i = 0; i < fileSize; i++)
            {
                downloadSocket.Receive(buffer, 1, SocketFlags.None);                                                 //Przesyłanie zipa na nowym porcie
                result.Add(buffer[0]);
            }

            SendMessage("SUCCESS\r\n\r\n", downloadSocket);                                                             //SUCCESS\r\n\r\n
            return result;
        }

        static void SendMessage(string message, Socket socket)
        {
            socket.Send(Encoding.UTF8.GetBytes(message));
        }

        static string ReceiveDataInString(Socket socket, byte[] endCode)
        {
            List<byte> receiveDataInBytes = ReceiveDataInBytes(socket, endCode);
            return Encoding.UTF8.GetString(receiveDataInBytes.ToArray());
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
            foreach (var modifiedFile in modifiedFiles)
            {
                Console.WriteLine(
                    $"{DateTime.Now} {modifiedFile.FilePath}: {modifiedFile.ModificationType.ToString()}");
            }

            SendMessage("CHANGE __SESIONID__ __PORT__  __ROZMIAR__", Server);

            ZipFile.CreateFromDirectory(_userName, $"{_userName}.zip");
            var zipInBytes = new FileInfo($"{_userName}.zip").Length;
            int randPort = new Random().Next(10000, 65535);

            var sendFileSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            var sendFileEndPoint = new IPEndPoint(ServerIp, randPort);

            sendFileSocket.Bind(sendFileEndPoint);
            sendFileSocket.Listen(1);

            SendMessage($"CHANGE {_sessionId} {randPort}  {zipInBytes}\r\n\r\n",
                Server);                                                                                                //CHANGE __SESIONID__ __PORT__  __ROZMIAR__

            var sendFileClient = sendFileSocket.Accept();
            var message = ReceiveDataInString(sendFileClient, EndCode);
            if (message != "READY")                                                                                     //READY\r\n\r\n
            {
                return;
            }

            sendFileClient.SendFile($"{_userName}.zip");                                                                //Przesyłanie zipa na nowym porcie

            if (message == "SUCCESS")                                                                                   //SUCCESS\r\n\r\n
            {
            }

            sendFileClient.Close();
        }
    }
}