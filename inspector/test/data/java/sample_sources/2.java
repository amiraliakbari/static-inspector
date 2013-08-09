class Fibonacci {
// Print out the Fibonacci sequence for values < 50
public static void main(String[] args) {
   int lo = 1;
   int hi = 1;
   System.out.println(lo);
   while (hi < 50) {
      System.out.print(hi);
      hi = lo + hi; // new hi
      lo = hi - lo; /* new lo is (sum - old lo)
                       i.e., the old hi */
   }
}
