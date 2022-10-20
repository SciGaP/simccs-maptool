/**
 * Return true if both sets are equal.
 * @param {Set} s1
 * @param {Set} s2
 */
function setsAreEqual(s1, s2) {
    if (s1.size !== s2.size) {
        return false;
    }
    for (let item of s1) {
        if (!s2.has(item)) {
            return false;
        }
    }
    return true;
}

function get_max_capture_target(source_selection, capMaxFieldName) {
      let capTotal = 0;
      for (const source of source_selection) {
            const capMax = source.feature.properties[capMaxFieldName];
            capTotal += capMax;
      }
      return capTotal;
}

function get_total_field_cap(sink_selection, fieldCapFieldName) {
      let fieldCapTotal = 0;
      for (const sink of sink_selection) {
            const fieldCap = sink.feature.properties[fieldCapFieldName];
            fieldCapTotal += fieldCap;
      }
      return fieldCapTotal;
}

function get_max_project_period(sink_selection, captureTarget, fieldCapFieldName) {

      const fieldCapTotal = get_total_field_cap(sink_selection, fieldCapFieldName);
      return fieldCapTotal / captureTarget;
}

function validate_model_parameters(source_selection, sink_selection, numYears, captureTarget, {fieldCapFieldName = "fieldCap (MtCO2)", capMaxFieldName = "capMax (MtCO2/y)"} = {}) {
      const result = {};
      const max_capture_target = get_max_capture_target(source_selection, capMaxFieldName);
      const max_project_period = get_max_project_period(sink_selection, captureTarget, fieldCapFieldName);

      if (captureTarget > max_capture_target) {
            result.captureTarget = `Annual capture target exceeds total capMax of sources
                  (${max_capture_target.toFixed(2)})`;
      }

      if (numYears > max_project_period) {
            const fieldCapTotal = get_total_field_cap(sink_selection, fieldCapFieldName);
            result.projectPeriod =
                  `Total project storage exceeds available storage
                  (${fieldCapTotal.toFixed(2)}) of the sinks using current
                  project period and annual capture target`;
      }
      return result;
}

function is_float_string(value) {
      // https://stackoverflow.com/a/22100269
      return parseFloat(value) == value;
}

function isUnauthenticatedError(error) {

      return (
        AiravataAPI.errors.ErrorUtils.isUnauthenticatedError &&
        AiravataAPI.errors.ErrorUtils.isUnauthenticatedError(error)
      );
}
