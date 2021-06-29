package maptool;

import dataStore.DataStorer;

public class CostSurfaceData {

    private double[][] constructionCosts;
    // private double[][] rightOfWayCosts;
    private double[][] routingCosts;

    public void load(DataStorer dataStorer) {

        this.constructionCosts = dataStorer.getConstructionCosts();
        // this.rightOfWayCosts = dataStorer.getRightOfWayCosts();
        this.routingCosts = dataStorer.getRoutingCosts();
    }

    public void populate(DataStorer dataStorer) {
        dataStorer.setConstructionCosts(this.constructionCosts);
        // dataStorer.setRightOfWayCosts(this.rightOfWayCosts);
        dataStorer.setRoutingCosts(this.routingCosts);
    }

    public double[][] getConstructionCosts() {
        return constructionCosts;
    }

    public void setConstructionCosts(double[][] constructionCosts) {
        this.constructionCosts = constructionCosts;
    }

    // public double[][] getRightOfWayCosts() {
    //     return rightOfWayCosts;
    // }

    // public void setRightOfWayCosts(double[][] rightOfWayCosts) {
    //     this.rightOfWayCosts = rightOfWayCosts;
    // }

    public double[][] getRoutingCosts() {
        return routingCosts;
    }

    public void setRoutingCosts(double[][] routingCosts) {
        this.routingCosts = routingCosts;
    }
}
