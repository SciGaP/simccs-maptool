# SimCCS Map Tool

## Getting Started

1. Follow the instructions for installing the
   [Airavata Django Portal](https://github.com/apache/airavata-django-portal)
2. With the Django Portal virtual environment activated, clone this repo and
   install it into the portal's virtual environment

   ```
   git clone https://github.com/SciGaP/simccs-maptool.git
   cd simccs-maptool
   pip install -e .
   ```

3. Start (or restart) the Django Portal server.
4. Open <http://localhost:8000/maptool> in your browser.

## Django portal configuration

The following settings are relevant for the SimCCS Map Tool. These can be
specified in Django Portal's `settings_local.py` file.

- `JAVA_HOME` - the Java home directory. Defaults to the JAVA_HOME env variable
  if not set.
- `MAPTOOL_SETTINGS` - this is a dictionary of Map Tool specific settings:
  - `CPLEX_APPLICATION_ID` - The Airavata application module id of the Cplex
    application to launch.
  - `DATASETS_DIR` - Directory of datasets and their basedata (cost network).
  - `JAVA_OPTIONS` - JVM command line options. Defaults to `-Xmx4g`. May be a
    list or tuple to pass multiple options.
  - `MAX_CONCURRENT_JAVA_CALLS` - maximum concurrent calls into Java code
    allowed across all HTTP requests. Default to 1.

Example of custom settings in a `settings_local.py` file:

```python
JAVA_HOME = "/usr/java/default"
MAPTOOL_SETTINGS = {
    "CPLEX_APPLICATION_ID": "Cplex_a7eaf483-ab92-4441-baeb-2f302ccb2919",
    "DATASETS_DIR": "/data/simccs-datasets"
}
```

## Pyjnius - simccs.jar notes

### Installing dependencies

In your virtual environment install the following:

```
pip install cython
pip install pyjnius
```

### Building the SimCCS jar

#### Building simccs GitHub repo code

**Note: No longer need to build. Just grab the SimCCS.jar from
https://github.com/simccs/SimCCS/tree/master/store**

Clone https://github.com/simccs/SimCCS

Then copy `store/SimCCS.jar` to `simccs_maptool/simccs/lib/SimCCS.jar`.

### MacOS notes

I ran into issues and followed the suggestions here:
https://github.com/joeferner/node-java/issues/90#issuecomment-45613235

Edited `/Library/Java/JavaVirtualMachines/jdk1.8.0_121.jdk/Contents/Info.plist`
and added JNI to JVMCapabilities:

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
    os.path.join(os.getcwd(), "simccs_maptool", "simccs", "lib", "simccs-app-1.0-jar-with-dependencies.jar"),
)
from jnius import autoclass

basepath = os.path.join(os.getcwd(), "simccs_maptool", "simccs", "Datasets")
dataset = "SoutheastUS"
scenario = "scenario1"
DataStorer = autoclass("simccs.dataStore.DataStorer")
data = DataStorer(basepath, dataset, scenario)
Solver = autoclass("simccs.solver.Solver")
solver = Solver(data)
data.setSolver(solver)
candidate_graph = data.generateCandidateGraph()
```
