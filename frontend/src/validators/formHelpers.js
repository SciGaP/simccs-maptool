/**
 * Convert to validation state for use in Bootstrap Vue form.
 * @param {*} validation - Vuelidate validation model
 */
export function validateState(validation) {
  const { $dirty, $error } = validation;
  return $dirty ? !$error : null;
}
