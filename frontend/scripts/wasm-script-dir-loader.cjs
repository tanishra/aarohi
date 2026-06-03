module.exports = function (source) {
  var result = source.replace(
    /scriptDirectory\s*=\s*new\s+URL\(\s*"\."\s*,\s*_scriptName\s*\)\.href\s*;/,
    'scriptDirectory = "/_avatarkit/";',
  );
  if (result === source) {
    result = source.replace(
      /scriptDirectory\s*=\s*"";/,
      'scriptDirectory = "/_avatarkit/";',
    );
  }
  return result;
};
