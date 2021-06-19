using System;
using System.IO;
using System.Timers;

namespace Client
{
    public class FileWatcher : IDisposable
    {
        private readonly TimeSpan _timeToRaiseEvent;
        private readonly FileSystemWatcher _fileSystemWatcher;
        private Timer _lastModificationTimer;
        private readonly object _lockObject = new();

        public delegate void FilesModifiedEventHandler();
        public event FilesModifiedEventHandler FilesModified;

        public FileWatcher(string directory, TimeSpan timeToRaiseEvent)
        {
            _timeToRaiseEvent = timeToRaiseEvent;

            _fileSystemWatcher = new FileSystemWatcher(directory)
            {
                IncludeSubdirectories = true
            };

            _fileSystemWatcher.Changed += OnFileChanged;
            _fileSystemWatcher.Created += OnFileChanged;
            _fileSystemWatcher.Deleted += OnFileChanged;
            _fileSystemWatcher.Renamed += OnFileChanged;
        }

        public void StartWatching()
        {
            _fileSystemWatcher.EnableRaisingEvents = true;
        }

        public void StopWatching()
        {
            _fileSystemWatcher.EnableRaisingEvents = false;
        }

        private void OnFileChanged(object sender, FileSystemEventArgs e)
        {
            StartOrResetModificationTimer();
        }

        private void StartOrResetModificationTimer()
        {
            lock (_lockObject)
            {
                _lastModificationTimer?.Dispose();
                _lastModificationTimer = new Timer
                {
                    Interval = _timeToRaiseEvent.TotalMilliseconds
                };
                _lastModificationTimer.Elapsed += OnLastModificationTimeElapsed;
                _lastModificationTimer.Start();
            }
        }

        private void OnLastModificationTimeElapsed(object sender, ElapsedEventArgs e)
        {
            FilesModified?.Invoke();
            _lastModificationTimer.Stop();
        }
        
        public void Dispose()
        {
            _fileSystemWatcher.Dispose();
            _lastModificationTimer?.Dispose();
        }
    }
}