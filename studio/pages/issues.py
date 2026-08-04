import pandas as pd
import streamlit as st
from studio.components import section,empty
from studio.data import status_group

def render(ctx):
    df=ctx.data[2];section('Результаты, требующие решения','Расхождения и неподтверждённые сведения без совпадений и служебных находок.')
    if df.empty or 'status' not in df:return empty('Замечания пока не сформированы.')
    view=df.copy();view['_group']=view.status.map(status_group);view=view[view._group.isin(['bad','warn'])]
    if view.empty:return st.success('Результаты, требующие решения, не выявлены.')
    opts=sorted(view.get('priority',pd.Series(dtype=str)).dropna().astype(str).unique());sel=st.multiselect('Приоритет',opts,default=opts)
    if sel and 'priority' in view:view=view[view.priority.isin(sel)]
    cols=['object','parameter_name','status','priority','document_values','explanation','sources'];labels={'object':'Объект','parameter_name':'Характеристика','status':'Статус','priority':'Приоритет','document_values':'Значения по разделам','explanation':'Почему требуется проверка','sources':'Источники'}
    st.dataframe(view[[c for c in cols if c in view]].rename(columns=labels),use_container_width=True,hide_index=True)
    st.download_button('Скачать перечень замечаний',data=view.drop(columns=['_group'],errors='ignore').to_csv(index=False).encode('utf-8-sig'),file_name='ExpertCheck_remarks.csv',mime='text/csv')
