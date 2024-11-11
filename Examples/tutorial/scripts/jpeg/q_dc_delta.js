// ./bin/fflive -i lena.jpg -s scripts/jpeg/q_dc_delta.js

/*********************************************************************/
// new DC delta value
const plane = 1; // EXPERIMENT BY CHANGING THIS VALUE FROM 0 to 2
const mb_x = 16; // EXPERIMENT BY CHANGING THIS VALUE
const mb_y = 16; // EXPERIMENT BY CHANGING THIS VALUE
const dc_delta = 63; // EXPERIMENT BY CHANGING THIS VALUE

/*********************************************************************/
export function setup(args)
{
  // select quantized dc delta feature
  args.features = [ "q_dc_delta" ];
}

export function glitch_frame(frame, stream)
{
  const data = frame.q_dc_delta.data;
  // change the DC delta value of the specified plane and macroblock
  data[plane][mb_x][mb_y] = dc_delta;
}
