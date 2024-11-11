// dd_randomiser.js

let randomness = 10;
let bias = (randomness / 2);

export function setup(args)
{
    args.features = [ "mv" ];

    // Pass "-sp <value>" in the command line, where <value> is an
    // integer.
    if ( "params" in args )
    {
        randomness = args.params;
        bias = (randomness / 2);
    }
}

export function glitch_frame(frame)
{
    // bail out if we have no forward motion vectors
    const fwd_mvs = frame.mv?.forward;
    if ( !fwd_mvs )
        return;

    // set motion vector overflow behaviour in ffedit to "truncate"
    frame.mv.overflow = "truncate";

    fwd_mvs.forEach((mv, i, j) => {
        mv[0] += Math.floor((Math.random() * randomness) - bias);
        mv[1] += Math.floor((Math.random() * randomness) - bias);
    });
}
