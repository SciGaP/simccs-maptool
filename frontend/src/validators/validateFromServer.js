/**
 * Vuelidate custom validator. Checks for server side validation errors.
 * Returns true if the value is different from the submitted value or if there
 * are no validation errors. Validation errors are assumed to be an array.
 */
export default (submittedValueGetter, validationErrorsGetter) => (value) => {
  const submittedValue = submittedValueGetter();
  const validationErrors = validationErrorsGetter();
  return (
    !submittedValue ||
    submittedValue !== value ||
    !validationErrors ||
    validationErrors.length === 0
  );
};
