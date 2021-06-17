using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Timers;
using Client.Extensions;

namespace Client.FileWatcherLibrary
{
    public class FileWatcher : IDisposable
    {
        private readonly TimeSpan _timeToRaiseEvent;
        private readonly FileSystemWatcher _fileSystemWatcher;
        private readonly ConcurrentDictionary<string, FileModificationType> _modificationTypeByFilePath = new();
        private Timer _lastModificationTimer;
        private readonly object _lockObject = new();

        public delegate void FilesModifiedEventHandler(IEnumerable<ModifiedFile> modifiedFiles);

        public event FilesModifiedEventHandler FilesModified;

        public FileWatcher(string directory, TimeSpan timeToRaiseEvent)
        {
            _timeToRaiseEvent = timeToRaiseEvent;

            _fileSystemWatcher = new FileSystemWatcher(directory)
            {
                IncludeSubdirectories = true
            };

            _fileSystemWatcher.Changed += OnFileChanged;
            _fileSystemWatcher.Created += OnFileCreated;
            _fileSystemWatcher.Deleted += OnFileDeleted;
            _fileSystemWatcher.Renamed += OnFileRenamed;
        }

        public void StartWatching()
        {
            _fileSystemWatcher.EnableRaisingEvents = true;
        }

        public void StopWatching()
        {
            _fileSystemWatcher.EnableRaisingEvents = false;
        }


        private void OnFileCreated(object sender, FileSystemEventArgs e)
        {
            if (IsDirectory(e.FullPath))
            {
                return;
            }
            _modificationTypeByFilePath.AddOrUpdate(e.FullPath, FileModificationType.Created);
            StartOrResetModificationTimer();
        }

        private void OnFileChanged(object sender, FileSystemEventArgs e)
        {
            if (IsDirectory(e.FullPath) || IsFileRecentlyCreated(e.FullPath))
            {
                return;
            }

            _modificationTypeByFilePath.AddOrUpdate(e.FullPath, FileModificationType.Changed);
            StartOrResetModificationTimer();
        }

        private void OnFileDeleted(object sender, FileSystemEventArgs e)
        {
            if (IsFileRecentlyCreated(e.FullPath) || IsFileRecentlyUpdated(e.FullPath))
            {
                _modificationTypeByFilePath.Remove(e.FullPath);
            }

            _modificationTypeByFilePath.AddOrUpdate(e.FullPath, FileModificationType.Deleted);
            StartOrResetModificationTimer();
        }

        private void OnFileRenamed(object sender, RenamedEventArgs e)
        {
            if (IsFileRecentlyCreated(e.OldFullPath) || IsFileRecentlyUpdated(e.OldFullPath))
            {
                _modificationTypeByFilePath.Remove(e.OldFullPath);
            }
            else
            {
                _modificationTypeByFilePath.AddOrUpdate(e.OldFullPath, FileModificationType.Deleted);
            }

            _modificationTypeByFilePath.AddOrUpdate(e.FullPath, FileModificationType.Created);
            StartOrResetModificationTimer();
        }

        private bool IsFileRecentlyCreated(string filePath)
        {
            return _modificationTypeByFilePath.ContainsKey(filePath) &&
                   _modificationTypeByFilePath[filePath] == FileModificationType.Created;
        }

        private bool IsFileRecentlyUpdated(string filePath)
        {
            return _modificationTypeByFilePath.ContainsKey(filePath) &&
                   _modificationTypeByFilePath[filePath] == FileModificationType.Created;
        }

        private bool IsDirectory(string path)
        {
            return string.IsNullOrEmpty(Path.GetFileName(path)) || Directory.Exists(path);
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
            var modifiedFiles = _modificationTypeByFilePath.Select(x => new ModifiedFile(x.Key, x.Value));
            FilesModified?.Invoke(modifiedFiles);

            _modificationTypeByFilePath.Clear();
            _lastModificationTimer.Stop();
        }


        public void Dispose()
        {
            _fileSystemWatcher.Dispose();
            _lastModificationTimer?.Dispose();
        }
    }
}