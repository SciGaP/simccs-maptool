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
