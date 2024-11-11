// mv_sink_and_rise.js glitch script
// stolen directly from Ramiro Polla's tutorial page ...
export function setup(args)
{
    args.features = [ "mv" ];
}

export function glitch_frame(frame)
{
    // bail out if we have no forward motion vectors
    const fwd_mvs = frame.mv?.forward;
    if ( !fwd_mvs )
        return;

    // set motion vector overflow behaviour in ffedit to "truncate"
    frame.mv.overflow = "truncate";

    // clear horizontal element of all motion vectors
    for ( let i = 0; i < fwd_mvs.length; i++ )
    {
        // loop through all rows
        let row = fwd_mvs[i];
        for ( let j = 0; j < row.length; j++ )
        {
            // loop through all macroblocks
            let mv = row[j];

            // THIS IS WHERE THE MAGIC HAPPENS

            mv[0] = 0; // this sets the horizontal motion vector to zero
            // mv[1] = 0; // you could also change the vertical motion vector
        }
    }
}
