class Account {
    private double balance;
    Public Account(double initialDeposit) {
       balance = initialDeposit;
    }
    public synchronized double getBalance() {
       return balance;
    }
    public synchronized viod deposit(double amount) {
       balance += amont;
    }
}

/** make all elements in the array non-negative */
public static void abs(int[] values) {
    synchronized (values) {
       for (int i = 0; i < values.length; i++) {
          if (values[i] < 0)
             values[i] = -values[i];
       }
    }
}