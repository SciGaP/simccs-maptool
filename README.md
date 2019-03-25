
## Pyjnius - simccs.jar notes

### Installing dependencies

In your virtual environment install the following:

```
pip install cython
pip install pyjnius
```

### Building the SimCCS jar

Clone https://github.com/simccs/SimCCS

```
cd SimCCS/
mkdir build 
find src -name "*.java" | xargs javac -cp ext/openmap.jar -d build/
find build/ -name "*.class" | xargs jar cvf build/SimCCS.jar -C build/
```

Then copy `build/SimCCS.jar` to `simccs_maptool/simccs/lib/SimCCS.jar`.

### MacOS notes

I ran into issues and followed the suggestions here: https://github.com/joeferner/node-java/issues/90#issuecomment-45613235

Edited `/Library/Java/JavaVirtualMachines/jdk1.8.0_121.jdk/Contents/Info.plist` and added JNI to JVMCapabilities:

```xml
...
<key>JVMCapabilities</key>
<array>
        <string>CommandLine</string>
        <string>JNI</string>
</array>
...
```

### Testing Pyjnius

You should be able to run the following with your virtual environment activated:

```python
import jnius_config
import os

jnius_config.set_classpath(
    os.path.join(os.getcwd(), "simccs_maptool", "simccs", "lib", "SimCCS.jar"),
    os.path.join(os.getcwd(), "simccs_maptool", "simccs", "lib", "openmap.jar"),
)
from jnius import autoclass

basepath = os.path.join(os.getcwd(), "simccs_maptool", "simccs", "Datasets")
dataset = "SoutheastUS"
scenario = "scenario1"
DataStorer = autoclass("dataStore.DataStorer")
data = DataStorer(basepath, dataset, scenario)
Solver = autoclass("solver.Solver")
solver = Solver(data)
data.setSolver(solver)
candidate_graph = data.generateCandidateGraph()
```