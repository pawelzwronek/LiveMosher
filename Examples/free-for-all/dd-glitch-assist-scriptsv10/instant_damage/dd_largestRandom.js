// dd_largestRandom.js
// only fuck things up if mv > movement_threshold
var LARGEST = 0;
var SOME_PERCENTAGE = 0.85; // only the fastest 15% of mv's in each frame get glitched

export function setup(args)
{
    args.features = [ "mv" ];

    // Pass "-sp <value>" in the command line, where <value> is an
    // integer from 0 to 100.
    if ( "params" in args )
        SOME_PERCENTAGE = (100 - args.params) / 100;
}

export function glitch_frame(frame)
{
    LARGEST = 0;
    // bail out if we have no forward motion vectors
    const fwd_mvs = frame.mv?.forward;
    if ( !fwd_mvs )
        return;

    // set motion vector overflow behaviour in ffedit to "truncate"
    frame.mv.overflow = "truncate";

    const largest = fwd_mvs.largest_sq();
    const threshold = Math.floor(SOME_PERCENTAGE * largest[2]);
    const mask = fwd_mvs.compare_gt(threshold);

    fwd_mvs.maskedForEach(mask, (mv) => {
        mv[0] += (Math.random() * 100) - 50;
        mv[1] += (Math.random() * 100) - 50;
    });
}
