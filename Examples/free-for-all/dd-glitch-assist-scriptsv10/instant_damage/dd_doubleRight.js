// dd_doubleRight.js
// every mv on the right of the frame is multiplied by 2

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

    const MID_POINT = fwd_mvs.width / 2;
    const subarray = fwd_mvs.subarray([MID_POINT, 0]);
    subarray.mul(2, 2);
}
