// ./bin/fflive -i CEP00109_mpeg4.avi -s scripts/mpeg4/mv_sink_and_rise.js

/*********************************************************************/
// Go down to WHERE THE MAGIC HAPPENS to experiment with this script.

/*********************************************************************/
export function setup(args)
{
  // select motion vector feature
  args.features = [ "mv" ];
}

export function glitch_frame(frame)
{
  const fwd_mvs = frame.mv?.forward;
  // bail out if we have no forward motion vectors
  if ( !fwd_mvs )
      return;

  // clear horizontal element of all motion vectors
  for ( let i = 0; i < fwd_mvs.length; i++ )
  {
    // loop through all rows
    const row = fwd_mvs[i];
    for ( let j = 0; j < row.length; j++ )
    {
      // loop through all macroblocks
      const mv = row[j];

      // THIS IS WHERE THE MAGIC HAPPENS

      mv[0] = 0; // this sets the horizontal motion vector to zero
      // mv[1] = 0; // you could also change the vertical motion vector
    }
  }
}
