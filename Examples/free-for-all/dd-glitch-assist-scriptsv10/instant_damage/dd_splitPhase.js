// dd_splitPhase.js
// alternates between blocking horizontal or veritcal elements of mv
// switch happens every (phase) frames

let frames_per_phase = 5;

let phase = true;
let count = 0;

export function setup(args)
{
    args.features = [ "mv" ];

    // Pass "-sp <value>" in the command line, where <value> is an
    // integer.
    if ( "params" in args )
        frames_per_phase = args.params;
}

export function glitch_frame(frame)
{
    // bail out if we have no forward motion vectors
    const fwd_mvs = frame.mv?.forward;
    if ( !fwd_mvs )
        return;

    // set motion vector overflow behaviour in ffedit to "truncate"
    frame.mv.overflow = "truncate";

    if ( phase )
        fwd_mvs.assign_h(0);
    else
        fwd_mvs.assign_v(0);

    if ( count++ >= frames_per_phase )
    {
        phase = !phase;
        count = 0;
    }
}
