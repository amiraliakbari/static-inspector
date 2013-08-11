class Point {
   public double x, y;
   public static Point origin = new Point(0,0);
     // This always refers to an object at (0,0)
   Point(double x_value, double y_value) {
      x = x_value;
      y = y_value;
   }
   public void clear() {
      // to be overridden
      this.x = 0;
      this.y = 0;
   }
   public double distance(Point that) {
      double xDiff = x - that.x;
      double yDiff = y - that.y;
      return Math.sqrt(xDiff * xDiff + yDiff * yDiff);
   }
}

class Pixel extends Point {
  Color color;

  public void clear() {
     super.clear();
     color = null;
  }
}