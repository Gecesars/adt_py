# Visual and Binary Export Notes

The legacy reference generator in this comparison folder rebuilds the engineering and text-based exports directly from the recovered ADT source logic.

For the visual exports below, the original ADT depends on chart/report rendering paths that are not yet replayed headlessly here:

- `HRP JPEG`: Legacy source method: FormFuncs.CreateHRPplot
- `VRP JPEG`: Legacy source method: FormFuncs.CreateVRPplot
- `Layout JPEG`: Legacy source method: layout image export from MainForm / Layout3D renderer
- `Summary PDF`: Legacy source method: FormFuncs.CreateResultSumpdf
- `Panel PDF`: Legacy source method: FormFuncs.CreatePanelPospdf
- `All PDF`: Legacy source methods: CreateHRPTabupdf + CreateVRPTabupdf + CreateResultSumpdf + CreatePanelPospdf + CreatePatLayoutPage
- `Video`: Legacy source path: VRP animation export from MainForm with temporary frame generation
