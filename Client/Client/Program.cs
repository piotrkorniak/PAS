using System;
using System.Collections.Generic;
using System.ComponentModel;
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
        private const int ServerPort = 1000;
        private static readonly byte[] EndCode = Encoding.UTF8.GetBytes("\r\n\r\n").ToArray();

        private static readonly Socket Server = new Socket(AddressFamily.InterNetwork, SocketType.Stream,
            ProtocolType.Tcp);

        private static string _userName;

        static void Main(string[] args)
        {
            Server.Connect(IPAddress.Loopback, ServerPort);
            //TODO: wymiana klucza publciznego
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

                SendMessage($"\"{_userName}\" \"{password}\"", Server, EndCode);

                var message = ReceiveDataInString(Server, EndCode);

                if (message == "404 BAD PASSWORD")
                {
                    continue;
                }

                if (message == "240 LOGGED IN")
                {
                    break;
                }
            }

            //TODO: do uzgodnienia przesyłanie plików
            int port = int.Parse(ReceiveDataInString(Server, EndCode));
            int directoryInZipLength = int.Parse(ReceiveDataInString(Server, EndCode));
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
                var request = ReceiveDataInString(socket, EndCode);
                var requestCode = int.Parse(request.Split().First());
                if (requestCode == 103)
                {
                }
            }
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

            List<byte> result = new List<byte>();
            byte[] buffer = new Byte[1];

            for (int i = 0; i < fileSize; i++)
            {
                downloadSocket.Receive(buffer, 1, SocketFlags.None);
                result.Add(buffer[0]);
            }

            return result;
        }

        static void SendMessage(string message, Socket socket, byte[] endCode)
        {
            socket.Send(Encoding.UTF8.GetBytes(message));
            socket.Send(endCode);
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
            SendMessage("Rozpocznij synchronizacje", Server, EndCode);
        }
    }
}