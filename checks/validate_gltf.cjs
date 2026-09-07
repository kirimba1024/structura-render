const fs = require('node:fs/promises');
const path = require('node:path');
const validator = require('gltf-validator');

async function main() {
  const filename = path.resolve(process.argv[2]);
  const directory = path.dirname(filename);
  const report = await validator.validateBytes(new Uint8Array(await fs.readFile(filename)), {
    uri: path.basename(filename),
    maxIssues: 100,
    externalResourceFunction: async (uri) => {
      const resource = path.resolve(directory, decodeURIComponent(uri));
      if (!resource.startsWith(directory + path.sep)) throw new Error('Resource outside asset directory');
      return new Uint8Array(await fs.readFile(resource));
    },
  });
  process.stdout.write(JSON.stringify(report));
  process.exitCode = report.issues.numErrors || report.issues.numWarnings ? 1 : 0;
}

main().catch((error) => {
  process.stderr.write(String(error));
  process.exitCode = 1;
});
