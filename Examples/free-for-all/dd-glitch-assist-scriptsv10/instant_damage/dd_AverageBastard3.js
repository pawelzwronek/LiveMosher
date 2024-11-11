// dd_AverageBastard3

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

    let sumX = 0;
    let sumY = 0;
    fwd_mvs.forEach((mv) => {
        sumX += mv[0];
        sumY += mv[1];
    });
    const length = fwd_mvs.height * fwd_mvs.width;
    sumX = Math.floor(sumX / length);
    sumY = Math.floor(sumY / length);

    // attack the mvs
    fwd_mvs.forEach((mv) => {
        mv[0] += sumX;
        mv[1] += sumY;
    });
}
