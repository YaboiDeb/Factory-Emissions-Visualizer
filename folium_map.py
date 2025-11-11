import base64
import folium
import matplotlib.pyplot as plt
import numpy as np
from folium.plugins import HeatMap         # still handy if you decide to use it
from io import BytesIO


def create_map(lat: float, lon: float,
        lst_array: np.ndarray,
        anomaly_indices: np.ndarray | list[int]):

        m = folium.Map(location=[lat, lon], zoom_start=12, control_scale=True)


        fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
        ax.axis('off')
        im = ax.imshow(lst_array, cmap='hot', vmin=np.nanmin(lst_array),
                vmax=np.nanmax(lst_array))

        # overlay the anomaly pixels in cyan
        if len(anomaly_indices):
                yy, xx = np.unravel_index(anomaly_indices, lst_array.shape)
                ax.scatter(xx, yy, s=6, alpha=0.6, linewidths=0,
                        marker='o', edgecolors='none', c='cyan')

        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")

        
        img_url = f"data:image/png;base64,{encoded}"
        span_deg = 0.05          
        bounds = [[lat - span_deg, lon - span_deg],
                [lat + span_deg, lon + span_deg]]

        folium.raster_layers.ImageOverlay(
                image=img_url,
                bounds=bounds,
                opacity=0.60,
                interactive=False
        ).add_to(m)

        folium.Marker([lat, lon],
                        tooltip="Factory Location",
                        icon=folium.Icon(color="red", icon="industry", prefix="fa")
                        ).add_to(m)

        return m
