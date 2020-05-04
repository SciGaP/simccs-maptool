
simccs_maptool/simccs/lib/maptool.jar: java/maptool/CostSurfaceData.class
	jar cf simccs_maptool/simccs/lib/maptool.jar -C java maptool/CostSurfaceData.class

java/maptool/CostSurfaceData.class: java/maptool/CostSurfaceData.java
	javac -cp simccs_maptool/simccs/lib/SimCCS.jar java/maptool/CostSurfaceData.java

clean:
	rm -f simccs_maptool/simccs/lib/maptool.jar
	rm -f java/maptool/CostSurfaceData.class
