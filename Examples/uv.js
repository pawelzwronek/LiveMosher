// This is an example of a vf_script feature
// Doc: https://ffglitch.org/docs/0.10.2/ffgac/#vf_script
// It is a simple filter that draws a color plane for the U and V planes

export function filter(args)
{
  let data = args["data"];
  // planes are [ Y, U, V ]
  const plen = data.length;
  for ( let p = 0; p < plen; p++ )
  {
    // skip plane Y, leave it as-is
    if ( p == 0 )
      continue;
    // for planes U and V, draw a color plane
    let plane = data[p];
    const ilen = plane.length;
    for ( let i = 0; i < ilen; i++ )
    {
      let row = plane[i];
      const jlen = row.length;
      for ( let j = 0; j < jlen; j++ )
      {
        if ( p == 1 )
          row[j] = j+j;
        else
          row[j] = 254-(i+i);
      }
    }
  }
}
