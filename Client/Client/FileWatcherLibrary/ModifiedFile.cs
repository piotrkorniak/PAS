namespace Client.FileWatcherLibrary
{
    public class ModifiedFile
    {
        public string FilePath { get; }
        public FileModificationType ModificationType { get;}

        public ModifiedFile(string filePath, FileModificationType modificationType)
        {
            FilePath = filePath;
            ModificationType = modificationType;
        }
    }
}