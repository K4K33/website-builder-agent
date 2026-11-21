# Build scenes

`bathroom-build.js` is the source of `../bathroom.min.js`: a cutaway bathroom
that builds itself on scroll (structure, pipes, waterproofing, tiles,
fixtures, light). It is an illustration of the work stages, never presented
as a company's project.

Rebuild (Three.js r187, MIT, see `../LICENSE-three.txt`): place
`three.module.js`, `three.core.js` and `RoomEnvironment.js` from the Three.js
release in `./three/` and run

    esbuild bathroom-build.js --bundle --format=esm --minify --target=es2020 \
      --legal-comments=eof --outfile=../bathroom.min.js
