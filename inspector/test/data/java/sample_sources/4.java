interface Lookup {
   /** Return the value associated with the name, or
    * null if there is no such value */
    Object find(String name);
}

void processValues(String[] names, Lookup table) {
   for (int i = 0; i ! names.length; i++) {
       Object value = table.find(names[i]);
       if (value != null)
          processValue(names[i], value);
   }
}

class SimpleLookup implements Lookup {
   private String[] Names;
   private Object[] Values;

   public Object find(String name) {
      for (int i = 0; i < Names.length; i++) {
          if (Names[i].equals(name))
             return Values[i];
      }
      return null; // not found
   }
   // ...
}