public class PingPONG extends Thread {
    private String word; // What word to print
    private int delay; // how long to pause
    public PingPONG(String whatToSay, int delayTime) {
        word = whatToSay;
        delay = delayTime;
    }
    public void run() {
        try {
            for (;;) {
                System.out.print(word + " ");
                sleep(delay); // wait until next time
            }
        } catch (InterruptedException e) {
            return; // end this thread;
        }
    }
    public static void main(String[] args) {
        new PingPONG("Ping", 33).start(); // 1/30 second
        new PingPONG("PONG",100).start(); // 1/10 second
    }
}
