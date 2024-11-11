// ./bin/fflive -i lena.png -s scripts/png/idat.js

/*********************************************************************/
// these constants are part of the PNG specification
// DO NOT CHANGE THESE VALUES HERE
// instead, change the `filter_type` constant below to any of these
// values here.
const PNG_FILTER_VALUE_NONE  = 0;
const PNG_FILTER_VALUE_SUB   = 1;
const PNG_FILTER_VALUE_UP    = 2;
const PNG_FILTER_VALUE_AVG   = 3;
const PNG_FILTER_VALUE_PAETH = 4;

/*********************************************************************/
// Uncomment **only one** of the lines below:
//
// const filter_type = PNG_FILTER_VALUE_NONE;
// const filter_type = PNG_FILTER_VALUE_SUB;
// const filter_type = PNG_FILTER_VALUE_UP;
// const filter_type = PNG_FILTER_VALUE_AVG;
const filter_type = PNG_FILTER_VALUE_PAETH;

export function setup(args)
{
  // select image data feature
  args.features = [ "idat" ];
}

export function glitch_frame(frame, stream)
{
  const rows = frame.idat?.rows;
  if ( !rows )
    return;
  const length = rows.length;
  // change the filter type for each row
  for ( let i = 0; i < length; i++ )
  {
    const row = rows[i];
    row[0] = filter_type;
  }
}
