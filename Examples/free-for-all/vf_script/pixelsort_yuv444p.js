
let options = {
  pix_fmt: "yuv",
  trigger_by: "y",
  sort_by: "y",
  order: "vertical",
  mode: "threshold",
  reverse_sort: false,
  threshold: [ 0.25, 0.80 ],
};

export function setup(args)
{
  args.pix_fmt = "yuv444p";
}

export function filter(args)
{
  let data = args["data"];
  const height = data[0].height;
  const width  = data[0].width;

  ffgac.pixelsort(data, [ 0, height ], [ 0, width ], options);
}
