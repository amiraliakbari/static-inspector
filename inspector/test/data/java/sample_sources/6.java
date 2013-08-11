class Account {
    private double balance;
    public Account(double initialDeposit) {
       balance = initialDeposit;
    }
    public synchronized double getBalance() {
       return balance;
    }
    public synchronized void deposit(double amount) {
       balance += amount;
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
}
