"""
Module for handling parameters in a flexible and extensible way.
"""

from typing import Optional, Any, Dict, Callable, Union
from abc import ABC, abstractmethod

class Collection(ABC):
    """
    Abstract base class for parameter collections.
    
    A collection provides a way to look up values by keys, with support for inheritance
    and composition through parent collections.
    """

    def __call__(self, key: str) -> Any:
        """
        Get a value by key from the collection.
        """
        return self.get(key)
    
    @abstractmethod
    def find(self, key: str, current: 'Collection', parent: 'Collection') -> Optional[Any]:
        """
        Find a value by key in the collection.
        
        Args:
            key: The key to look up
            current: The current collection being searched
            parent: The parent collection to fall back to if key is not found
            
        Returns:
            The value associated with the key, or None if not found
        """
        pass

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value by key from the collection.
        
        Args:
            key: The key to look up
            
        Returns:
            The value associated with the key, or None if not found
        """
        return self.find(key, self, EmptyCollection())

class EmptyCollection(Collection):
    """
    An empty collection that always delegates to its parent.
    
    This serves as the base case for collection inheritance chains.
    """
    
    def find(self, key: str, current: Collection, parent: Collection) -> Optional[Any]:
        """
        Always delegate to parent collection.
        
        Args:
            key: The key to look up
            current: The current collection (unused)
            parent: The parent collection to delegate to
            
        Returns:
            The value from the parent collection, or None if not found
        """
        return parent.get(key)

    def get(self, key: str) -> None:
        """
        Always return None as this is an empty collection.
        
        Args:
            key: The key to look up (unused)
            
        Returns:
            None
        """
        return None

class MapCollection(Collection):
    """
    A collection that stores values in a dictionary.
    """
    
    def __init__(self, map: Dict[str, Any]):
        """
        Initialize with a dictionary of key-value pairs.
        
        Args:
            map: Dictionary containing the key-value pairs
        """
        self.map = map
    
    def find(self, key: str, current: Collection, parent: Collection) -> Optional[Any]:
        """
        Look up key in the dictionary, fall back to parent if not found.
        
        Args:
            key: The key to look up
            current: The current collection (unused)
            parent: The parent collection to fall back to
            
        Returns:
            The value from the dictionary, or from parent if not found
        """
        if key in self.map:
            return self.map[key]
        return parent.get(key)

class PatternCollection(Collection):
    """
    A collection that uses a pattern function to determine values.
    """
    
    def __init__(self, pattern: Callable[[Collection, Collection], Callable[[str], Optional[Any]]]):
        """
        Initialize with a pattern function.
        
        Args:
            pattern: A function that takes current and parent collections and returns
                    a function that takes a key and returns a value
        """
        if not pattern.__code__.co_varnames == ('current', 'parent', 'key'):
            raise ValueError("Programmable parameter must take exactly three named arguments: current, parent, and key")
        self.pattern = pattern
    
    def find(self, key: str, current: Collection, parent: Collection) -> Optional[Any]:
        """
        Apply pattern function to determine value, fall back to parent if not found.
        
        Args:
            key: The key to look up
            current: The current collection
            parent: The parent collection to fall back to
            
        Returns:
            The value determined by the pattern, or from parent if not found
        """
        if self.pattern(current, parent, key):
            return self.pattern(current, parent, key)
        return parent.get(key)

class DerivedCollection(Collection):
    """
    A collection that combines a new collection with an old one.
    """
    
    def __init__(self, new: Collection, old: Collection):
        """
        Initialize with new and old collections.
        
        Args:
            new: The new collection to search first
            old: The old collection to fall back to
        """
        self.new = new
        self.old = old
    
    def find(self, key: str, current: Collection, parent: Collection) -> Optional[Any]:
        """
        Search in new collection first, then old collection.
        
        Args:
            key: The key to look up
            current: The current collection
            parent: The parent collection
            
        Returns:
            The value from new collection, or from old collection if not found
        """
        return self.new.find(key, current, DerivedCollection(self.old, parent))
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value by searching in new collection first, then old collection.
        
        Args:
            key: The key to look up
            
        Returns:
            The value from new collection, or from old collection if not found
        """
        return self.new.find(key, self, self.old)

class Parameter:
    """
    A class that manages parameter collections and provides a convenient interface.
    """
    
    def __init__(self, arg: Optional[Union[Dict[str, Any], Callable]] = None):
        """
        Initialize a Parameter with a collection.
        
        Args:
            arg: Optional argument to initialize the collection:
                - None: Creates an empty collection
                - dict: Creates a map collection
                - Callable: Creates a pattern collection
                
        Raises:
            TypeError: If arg is not None, dict, or Callable
        """
        match arg:
            case None:
                self.collection = EmptyCollection()
            case dict():
                self.collection = MapCollection(arg)
            case _:
                if not isinstance(arg, Callable):
                    raise TypeError("Unsupported argument type for Parameter initialization.")
                self.collection = PatternCollection(arg)

    def __call__(self, key: str) -> Any:
        """
        Get a value by key, raising KeyError if not found.
        
        Args:
            key: The key to look up
            
        Returns:
            The value associated with the key
            
        Raises:
            KeyError: If the key is not found
        """
        value = self.get(key)
        if value is None:
            raise KeyError(f"Key '{key}' not found in collection.")
        return value

    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Get a value by key with a default fallback.
        
        Args:
            key: The key to look up
            default: The default value to return if key is not found
            
        Returns:
            The value associated with the key, or default if not found
        """
        value = self.collection.find(key, self, EmptyCollection())
        if value is None:
            return default
        return value

    def __add__(self, other: Union['Parameter', Dict[str, Any], Callable]) -> 'Parameter':
        return self.update(other)

    def alter(self, new: Union['Parameter', Dict[str, Any], Callable]) -> 'Parameter':
        return self.update(new)

    def add(self, new: Union['Parameter', Dict[str, Any], Callable]) -> 'Parameter':
        return self.update(new)

    def update(self, new: Union['Parameter', Dict[str, Any], Callable]) -> 'Parameter':
        """
        Update the parameter with another parameter, dictionary, or callable.
        """
        if isinstance(new, Parameter):
            self.collection = DerivedCollection(new.collection, self.collection)
        elif isinstance(new, dict):
            self.collection = DerivedCollection(MapCollection(new), self.collection)
        else:
            if not isinstance(new, Callable): 
                raise TypeError("Can only add Parameter or dict to Parameter")
            self.collection = DerivedCollection(PatternCollection(new), self.collection)
        return self
