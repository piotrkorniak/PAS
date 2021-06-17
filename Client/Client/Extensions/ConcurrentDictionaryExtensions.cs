using System.Collections.Concurrent;
using System.Collections.Generic;

namespace Client.Extensions
{
    public static class ConcurrentDictionaryExtensions
    {
        public static void AddOrUpdate<TKey, TValue>(this ConcurrentDictionary<TKey, TValue> dict, TKey key, TValue value)
        {
            dict.AddOrUpdate(key, _ => value, (_, _) => value);
        }
        
        public static void Remove<TKey, TValue>(this ConcurrentDictionary<TKey, TValue> dict, TKey key)
        {
            dict.Remove(key, out var _);
        }
    }
}