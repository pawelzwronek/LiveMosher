/*********************************************************************/
/* motion vectors */
function get_mvs_internal(frame, overflow, which)
{
  // bail out if we have no motion vectors
  let mvs = frame["mv"];
  if ( !mvs )
    return;
  // bail out if we have no forward motion vectors
  let fwd_mvs = mvs[which];
  if ( !fwd_mvs )
    return;
  if ( overflow )
    mvs.overflow = overflow;
  return fwd_mvs;
}

/* Get forward motion vectors and set overflow flag */
export function get_forward_mvs(frame, overflow)
{
  return get_mvs_internal(frame, overflow, "forward");
}

/* Get backward motion vectors and set overflow flag */
export function get_backward_mvs(frame, overflow)
{
  return get_mvs_internal(frame, overflow, "backward");
}

function get_mvs_range_internal(frame, stream, which)
{
  // bail out if we have no motion vectors
  let mvs = frame["mv"];
  if ( !mvs )
    return;

  const fcode = mvs["fcode"][which];
  const bit_size = fcode - 1;
  const shift = (stream.codec == "mpeg2video") ? 5
              : (stream.codec == "mpeg4")      ? 6
              :                                  5;
  const min_val = -(1<<(shift+bit_size-1));
  const max_val =  (1<<(shift+bit_size-1))-1;

  return [ min_val, max_val ];
}

/* Get range for forward motion vectors */
export function get_forward_mvs_range(frame, stream)
{
  return get_mvs_range_internal(frame, stream, 0);
}

/* Get range for backward motion vectors */
export function get_backward_mvs_range(frame, stream)
{
  return get_mvs_range_internal(frame, stream, 1);
}

/*********************************************************************/
/* scales value from 'from' range to 'to' range */
export function scaleValue(value, from_min, from_max, to_min, to_max)
{
  return (value - from_min) * (to_max - to_min) / (from_max - from_min) + to_min;
}
