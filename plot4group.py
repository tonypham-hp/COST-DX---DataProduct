import streamlit as st  
import os  
import pandas as pd  
import plotly.graph_objects as go  
from plotly.subplots import make_subplots  
import numpy as np  
import glob  
from datetime import datetime


def plot_summary_stacked_PC(summary_df, folder_name):  
    fig = make_subplots(specs=[[{"secondary_y": True}]])  
    month_order = ["APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "JAN", "FEB", "MAR"]  
    fig.add_trace(go.Bar(  
        x=summary_df.index, y=summary_df['AP'], name='AP', marker_color='skyblue',  
        offsetgroup=0, hovertemplate='AP<br>%{y:.2f}<extra></extra>',  
        hoverlabel=dict(font=dict(color="black"), bgcolor='white')  
    ))  
    fig.add_trace(go.Bar(  
        x=summary_df.index,  
        y=summary_df['Xuất kho'],  
        name='Xuất kho - ACT',  
        marker_color='orange',  
        offsetgroup=1,  
        base=0,  
        hovertemplate='Xuất kho - ACT<br>%{y:.2f}<extra></extra>',  
        hoverlabel=dict(font=dict(color="black"), bgcolor='white')  
    ), secondary_y=False)  
  
    fig.add_trace(go.Bar(  
        x=summary_df.index,  
        y=summary_df['BEC'],  
        name='BEC - ACT',  
        marker_color='lightcoral',  
        offsetgroup=1,  
        base=summary_df['Xuất kho'],  
        text=[f"{y:,.0f}" for y in (summary_df['BEC'] + summary_df['Xuất kho'])],  
        textposition='outside',  
        textfont=dict(color='black'),  
        customdata=np.array(summary_df['BEC']).reshape(-1,1),  
        hovertemplate='BEC - ACT<br>%{customdata:.2f}<extra></extra>',  
        hoverlabel=dict(font=dict(color="black"), bgcolor='white')  
    ), secondary_y=False)  
  
    # Cộng dồn cho đường line  
    cumulative_act = summary_df['Xuất kho'].cumsum() + summary_df['BEC'].cumsum()  
    cumulative_ap = summary_df['AP'].cumsum()  
  
    fig.add_trace(go.Scatter(  
        x=summary_df.index,  
        y=cumulative_act,  
        mode='lines+markers',  
        name='Cumulative ACT',  
        line=dict(color='red'),  
        hovertemplate='Cumulative ACT<br>%{y:.2f}<extra></extra>',  
        hoverlabel=dict(font=dict(color="black"), bgcolor='white')  
    ), secondary_y=True)  
  
    fig.add_trace(go.Scatter(  
        x=summary_df.index,  
        y=cumulative_ap,  
        mode='lines+markers',  
        name='Cumulative AP',  
        line=dict(color='blue', dash='dot'),  
        hovertemplate='Cumulative AP<br>%{y:.2f}<extra></extra>',  
        hoverlabel=dict(font=dict(color="black"), bgcolor='white')  
    ), secondary_y=True)  
  
    fig.update_layout(  
        width=1920, height=500,  
        title=dict(text=f"Cost for {folder_name}", font=dict(color='black')),  
        xaxis=dict(tickfont=dict(color='black')),  
        yaxis=dict(tickfont=dict(color='black')),  
        yaxis2=dict(tickfont=dict(color='black')),  
        legend=dict(orientation='h', x=0.5, y=1.12, xanchor='center', yanchor='top'),  
        barmode='group',  
        template='plotly_white',  
        autosize=True,  
        margin=dict(t=80)  
    )  
    fig.update_traces(marker_line_color='black')  
    fig.update_xaxes(  
        tickvals=list(summary_df.index),  
        ticktext=list(summary_df.index),  
        tickmode='array',  
        tickangle=0,  
        linecolor='black',  
        ticks='outside',  
        ticklen=5,  
        tickwidth=0.2,  
        tickcolor='black',  
        showline=True  
    )  
    fig.update_yaxes(  
        ticks='inside',  
        ticklen=5,  
        tickwidth=0.2,  
        tickcolor='black',  
        showline=True,  
        linecolor='black',  
        secondary_y=False  
    )  
    fig.update_yaxes(  
        ticks='inside',  
        ticklen=5,  
        tickwidth=0.2,  
        tickcolor='black',  
        showline=True,  
        showgrid=False,  
        linecolor='black',  
        secondary_y=True  
    )  
    fig.add_annotation(  
        text="USD",  
        xref="paper", yref="paper",  
        x=-0.0219, y=1.04,  
        showarrow=False,  
        font=dict(size=11, color='black'),  
        align="left"  
    )  
    fig.add_annotation(  
        text="USD",  
        xref="paper", yref="paper",  
        x=0.963, y=1.04,  
        showarrow=False,  
        font=dict(size=11, color='black'),  
        align="right"  
    )  
    return fig

def plot_summary_stacked_TV(summary_df, folder_name):  
    fig = make_subplots(specs=[[{"secondary_y": True}]])  
    month_order = ["APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "JAN", "FEB", "MAR"] 
    # Thêm thanh bar cho "AP"  
    fig.add_trace(  
        go.Bar(  
            x=summary_df.index,  
            y=summary_df['AP'],  
            name='AP',  
            marker_color='skyblue',  
            offsetgroup=0,
            hovertemplate='AP<br>%{y:.2f}<extra></extra>',
            hoverlabel=dict(font=dict(color="black"), bgcolor='white')
        )  
    )  
  
       # Thêm thanh stacked bar cho "Xuất kho" và "BEC"  
    fig.add_trace(  
        go.Bar(  
            x=summary_df.index,  
            y=summary_df['Xuất kho'],  
            name='Xuất kho - ACT',  
            marker_color='orange',  
            offsetgroup=1,  
            base=0,
            hovertemplate='Xuất kho - ACT<br>%{y:.2f}<extra></extra>',
            hoverlabel=dict(font=dict(color="black"), bgcolor='white')
        ),secondary_y=False
    )  
  
    fig.add_trace(  
        go.Bar(  
            x=summary_df.index,  
            y=summary_df['BEC'],  
            name='BEC - ACT',  
            marker_color='lightcoral',  
            offsetgroup=1,  
            base=summary_df['Xuất kho'],
            text=[f"{y:,.0f}" for y in (summary_df['BEC']+ summary_df['Xuất kho'])],  
            textposition='outside',
            textfont=dict(color='black'),
            customdata=np.array(summary_df['BEC']).reshape(-1,1),
            hovertemplate='BEC - ACT<br>%{customdata:.2f}<extra></extra>',
            hoverlabel=dict(font=dict(color="black"), bgcolor='white'),
        ),secondary_y=False
    )  
  
    # Thêm biểu đồ đường cho "Cumulative ACT"  
    cumulative_act = summary_df['Xuất kho'].cumsum()  + summary_df['BEC'].cumsum()   
    fig.add_trace(  
        go.Scatter(  
            x=summary_df.index,  
            y=cumulative_act,  
            mode='lines+markers',  
            name='Cumulative ACT',  
            line=dict(color='red'),
            hovertemplate='Cumulative ACT<br>%{y:.2f}<extra></extra>',
            hoverlabel=dict(font=dict(color="black"), bgcolor='white')
        ),secondary_y=True,
    )  
  
    # Thêm biểu đồ đường cho "Cumulative AP"  
    cumulative_ap = summary_df['AP'].cumsum()  
    fig.add_trace(  
        go.Scatter(  
            x=summary_df.index,  
            y=cumulative_ap,  
            mode='lines+markers',  
            name='Cumulative AP',  
            line=dict(color='blue', dash='dot'),
            hovertemplate='Cumulative AP<br>%{y:.2f}<extra></extra>',
            hoverlabel=dict(font=dict(color="black"), bgcolor='white')
        ),secondary_y=True,
    )  
  
    # Cấu hình biểu đồ  
    fig.update_layout(
        width = 1920,
        height = 600,
        #title = dict(text=f"Cost for {folder_name}", font=dict(size=20, color='black')),
        xaxis = dict(tickfont = dict(color='black')),
        yaxis = dict(tickfont = dict(color='black')),
        yaxis2 = dict(tickfont = dict(color='black')),
        legend=dict(orientation='h' , x=0.5, y=1.2, xanchor='center', yanchor='top'),
        barmode='group',  
        template='plotly_white',
        autosize=True,
    )
    fig.update_traces(marker_line_color = 'black')
    fig.update_xaxes(  
    tickvals=list(month_order),   
    ticktext=list(month_order),   
    tickmode='array',  
    tickangle=0,                
    linecolor='black',  
    ticks='outside',  
    ticklen=5,  
    tickwidth=0.2,  
    tickcolor='black',  
    showline=True  
)  
    fig.update_yaxes(
    ticks='inside',        
    ticklen=5,              
    tickwidth=0.2,          
    tickcolor='black',  
    showline=True,  
    linecolor='black', 
    secondary_y=False
    )
    fig.add_annotation(  
        text="USD",  
        xref="paper", yref="paper",  
        x=-0.0219, y=1.04,  
        showarrow=False,  
        font=dict(size=11, color='black'),  
        align="left"
        )  
    fig.update_yaxes(  
    ticks='inside',        
    ticklen=5,              
    tickwidth=0.2,          
    tickcolor='black',  
    showline=True, 
    linecolor='black',   
    secondary_y=True,
    showgrid=False
    )
    fig.add_annotation(  
        text="USD",  
        xref="paper", yref="paper",  
        x=0.963, y=1.04,  
        showarrow=False,  
        font=dict(size=11, color='black'),  
        align="right"
        ) 
    # Hiển thị biểu đồ trong Streamlit

    return fig
    