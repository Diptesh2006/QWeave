"use strict";

const fs = require("fs");
const path = require("path");
const { mathjax } = require("mathjax-full/js/mathjax.js");
const { TeX } = require("mathjax-full/js/input/tex.js");
const { SVG } = require("mathjax-full/js/output/svg.js");
const { liteAdaptor } = require("mathjax-full/js/adaptors/liteAdaptor.js");
const { RegisterHTMLHandler } = require("mathjax-full/js/handlers/html.js");
const { AllPackages } = require("mathjax-full/js/input/tex/AllPackages.js");
const sharp = require("sharp");

const equations = [
  String.raw`J(m)=\sum_{(i,j)\in E_C} w_{ij}\,d_H\!\left(m(i),m(j)\right).\qquad (1)`,
  String.raw`U_{R_k}P_{m_0}=P_{m_k}U_{C_k},\qquad 0\leq k\leq T.\qquad (2)`,
  String.raw`r_i=d_i+\max_{j\in\operatorname{succ}(i)}r_j,\qquad s_i=\max_{j\in\operatorname{pred}(i)}\!\left(s_j+d_j\right).\qquad (3)`,
  String.raw`\operatorname{CX}_{u\rightarrow v}=(H_u\otimes H_v)\,\operatorname{CX}_{v\rightarrow u}\,(H_u\otimes H_v).\qquad (4)`,
];

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const input = new TeX({ packages: AllPackages, tags: "ams" });
// A self-contained SVG avoids MathJax's separate local font-cache SVG, which
// otherwise expands the raster canvas far beyond the equation bounds.
const output = new SVG({ fontCache: "none" });
const document = mathjax.document("", { InputJax: input, OutputJax: output });
const outputDirectory = path.join(__dirname, "assets");
fs.mkdirSync(outputDirectory, { recursive: true });

async function renderEquation(latex, index) {
  const container = document.convert(latex, { display: true });
  const svgNode = adaptor.firstChild(container);
  if (!svgNode) throw new Error(`MathJax did not emit SVG for equation ${index}`);
  let svg = adaptor.outerHTML(svgNode).replace(/<\?xml[^>]*>/g, "");
  if (!/xmlns="http:\/\/www\.w3\.org\/2000\/svg"/.test(svg)) {
    svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ');
  }
  svg = svg.replace("<svg ", '<svg color="#000000" ');
  const destination = path.join(outputDirectory, `equation_${index}.png`);
  await sharp(Buffer.from(svg), { density: 300 })
    .trim({ background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .extend({
      top: 28,
      bottom: 28,
      left: 36,
      right: 36,
      background: { r: 255, g: 255, b: 255, alpha: 1 },
    })
    .resize({ width: 1600, withoutEnlargement: true })
    .flatten({ background: "#ffffff" })
    .removeAlpha()
    .png()
    .toFile(destination);
  process.stdout.write(destination + "\n");
}

(async () => {
  for (let index = 0; index < equations.length; index += 1) {
    await renderEquation(equations[index], index + 1);
  }
})().catch((error) => {
  process.stderr.write(error.stack + "\n");
  process.exitCode = 1;
});
