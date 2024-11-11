// dd_delay.js
// works kinda like an audio delay
// stacks the previous n frames into a buffer

// try making the delay long enough to overlap an edit in the content ...
let delay = 20;

// global variable holding forward motion vectors from previous frames
let prev_fwd_mvs = [ ];

export function setup(args)
{
    args.features = [ "mv" ];

    // Pass "-sp <value>" in the command line, where <value> is an
    // integer.
    if ( "params" in args )
        delay = args.params;
}

export function glitch_frame(frame)
{
    // bail out if we have no forward motion vectors
    const fwd_mvs = frame.mv?.forward;
    if ( !fwd_mvs )
        return;

    // set motion vector overflow behaviour in ffedit to "truncate"
    frame.mv.overflow = "truncate";

    // update variable holding forward motion vectors from previous
    // frames. note that we perform a deep copy of the clean motion
    // vector values before modifying them.
    let deep_copy = fwd_mvs.dup();
    // push to the end of array
    prev_fwd_mvs.push(deep_copy);
    // drop values from earliest frames to always keep the same tail
    // length
    if ( prev_fwd_mvs.length > delay )
        prev_fwd_mvs = prev_fwd_mvs.slice(1);

    // bail out if we still don't have enough frames
    if ( prev_fwd_mvs.length != delay )
        return;

    fwd_mvs.assign(prev_fwd_mvs[0]);
}
