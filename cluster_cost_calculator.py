import streamlit as st
from math import ceil
import pandas as pd
import altair as alt

# Define the VMInstance class
class VMInstance:
    def __init__(self, name, vCPUs, DBUs, cost_per_hour, RAM_GB):
        self.name = name
        self.vCPUs = vCPUs
        self.DBUs = DBUs
        self.cost_per_hour = cost_per_hour
        self.RAM_GB = RAM_GB  # Memòria RAM en GB

# Define cost calculation functions
def calcular_cost_job_cluster(driver_cost_per_hour, worker_cost_per_hour, total_DBUs, cost_dbu_job, temps_overhead_min, temps_execucio_min, max_parallel_tasks, total_tasks):
    """
    Calcula el cost total per tasca en un Job Cluster, considerant una limitació de tasques en paral·lel.
    """
    # Nombre d'onades necessàries
    nombre_onades_job = ceil(total_tasks / max_parallel_tasks)
    
    # Temps total actiu incloent overhead
    temps_total_min_job = nombre_onades_job * (temps_overhead_min + temps_execucio_min)
    
    # Càlcul del Cost de les VM durant l'overhead i l'execució
    cost_vm_total_job = (temps_total_min_job / 60) * (driver_cost_per_hour + worker_cost_per_hour)
    
    # Càlcul del Cost de les DBUs durant l'execució
    cost_dbu_execucio_job = (temps_execucio_min / 60) * total_DBUs * cost_dbu_job * nombre_onades_job
    
    # Càlcul del Cost Total per Tasca
    cost_total_per_tasca_job = cost_vm_total_job + cost_dbu_execucio_job
    
    return cost_total_per_tasca_job, cost_vm_total_job, cost_dbu_execucio_job, temps_total_min_job, nombre_onades_job

def calcular_cost_all_purpose(driver_cost_per_hour, workers_cost_per_hour, total_DBUs, cost_dbu_all_purpose, temps_total_actiu_min):
    """
    Calcula el cost total en un All-Purpose Cluster.
    """
    # Càlcul del Cost de les DBUs per hora
    cost_dbu_all_purpose_per_hour = total_DBUs * cost_dbu_all_purpose

    # Càlcul del Cost de les VM per hora
    cost_vm_all_purpose_per_hour = driver_cost_per_hour + workers_cost_per_hour

    # Càlcul del Cost Total per hora All-Purpose
    cost_total_per_hour_all_purpose = cost_dbu_all_purpose_per_hour + cost_vm_all_purpose_per_hour

    # Càlcul del Cost Total All-Purpose durant l'Actiu
    cost_total_all_purpose = (temps_total_actiu_min / 60) * cost_total_per_hour_all_purpose

    return cost_total_all_purpose, cost_dbu_all_purpose_per_hour, cost_vm_all_purpose_per_hour, cost_total_per_hour_all_purpose

# Streamlit App
def main():
    # Configura la pàgina
    st.set_page_config(page_title="📊 Cluster Cost Calculator", layout="wide", initial_sidebar_state="expanded")
    
    # Títol principal amb Logo
    col_title, col_logo = st.columns([4, 1])  # Proporció 4:1 per tenir el títol més gran que el logo
    with col_title:
        st.title("📊 Cluster Cost Calculator")
    with col_logo:
        try:
            st.image("logo.png", width=200)  # Assegura't que 'logo.png' estigui al mateix directori
        except:
            st.write("![Logo](https://via.placeholder.com/200)")  # Placeholder si no es troba l'arxiu
    
    st.markdown("""
    Aquesta aplicació permet calcular els costos i els temps d'execució dels **Job Clusters** i **All-Purpose Clusters** segons la seva configuració i les tasques que han de realitzar.
    """)
    
    # Taula Resum dels Costos de les Instàncies
    st.header("📋 Resum dels Costos de les Instàncies")
    
    # Definir les instàncies disponibles (incloent RAM)
    instancies = [
        VMInstance('DS4_V2', 8, 1.5, 0.5219, 32),
        VMInstance('D4A_V4', 4, 0.75, 0.2207, 16),
        VMInstance('D8A_V4', 8, 1.5, 0.4414, 32),
        VMInstance('E4DS_V5', 4, 1.5, 0.3320, 24),
        VMInstance('D4DS_V5', 4, 1.0, 0.2610, 16)
    ]
    
    # Crear un DataFrame amb els detalls de les instàncies
    data_instances = pd.DataFrame({
        'Nom de la Instància': [inst.name for inst in instancies],
        'vCPUs': [inst.vCPUs for inst in instancies],
        'DBUs': [inst.DBUs for inst in instancies],
        '€/VMs-hora': [inst.cost_per_hour for inst in instancies],
        'RAM (GB)': [inst.RAM_GB for inst in instancies]
    })
    
    # Crear el DataFrame per als costos per tipus de càlcul
    data_compute_costs = pd.DataFrame({
        'Compute Type': ['All-Purpose Compute', 'Jobs Compute'],
        '€/DBU-hora': [
            f"{0.528:.3f}".replace('.', ',') + ' €',
            f"{0.288:.3f}".replace('.', ',') + ' €'
        ]
    })
    
    # Crear dues columnes per mostrar les dues taules una al costat de l'altra
    col_instances, col_compute_costs = st.columns(2)
    
    with col_instances:
        st.subheader("Instàncies Disponibles")
        st.table(data_instances)
    
    with col_compute_costs:
        st.subheader("Costos per Tipus de Càlcul")
        st.table(data_compute_costs)
    
    # Barra lateral per a inputs
    st.sidebar.header("🛠️ Configuració")
    
    # Selecció d'instància per al Job Cluster
    instance_names = [inst.name for inst in instancies]
    selected_instance_job = st.sidebar.selectbox("🔍 Tipus d'instància per al **Job Cluster**", instance_names, index=0)
    instancia_job = next(inst for inst in instancies if inst.name == selected_instance_job)
    
    # Selecció d'instància per a l'All-Purpose Cluster
    selected_instance_all_purpose = st.sidebar.selectbox("🔍 Tipus d'instància per a l'**All-Purpose Cluster**", instance_names, index=1)
    instancia_all_purpose = next(inst for inst in instancies if inst.name == selected_instance_all_purpose)
    
    st.sidebar.markdown("---")
    
    # Inputs de l'usuari
    temps_execucio_per_tasca_min = st.sidebar.number_input("⏱️ Temps d'execució per tasca (minuts)", min_value=0.1, value=10.0, step=0.1)
    nombre_tasques = st.sidebar.number_input("🔢 Nombre de tasques", min_value=1, value=100, step=1)
    nombre_workers_all_purpose = st.sidebar.number_input("👥 Nombre de workers (All-Purpose)", min_value=1, value=5, step=1)
    max_parallel_tasks_job = st.sidebar.number_input("⚙️ Nombre màxim de tasques en paral·lel (Job Cluster)", min_value=1, value=35, step=1)
    
    # Constants
    temps_overhead_min = 2.5
    cost_dbu_job = 0.288
    cost_dbu_all_purpose = 0.528
    
    # Configuració Job Cluster
    nodes_job_driver = 1
    nodes_job_workers = 1
    total_DBUs_job = (nodes_job_driver + nodes_job_workers) * instancia_job.DBUs
    cost_vm_job_driver = nodes_job_driver * instancia_job.cost_per_hour
    cost_vm_job_workers = nodes_job_workers * instancia_job.cost_per_hour
    cost_vm_job_total = cost_vm_job_driver + cost_vm_job_workers
    
    # Càlcul del cost per tasca en Job Cluster amb limitació de paral·lelisme
    cost_per_tasca_job, cost_vm_total_job, cost_dbu_execucio_job, temps_total_min_job, nombre_onades_job = calcular_cost_job_cluster(
        driver_cost_per_hour=cost_vm_job_driver,
        worker_cost_per_hour=cost_vm_job_workers,
        total_DBUs=total_DBUs_job,
        cost_dbu_job=cost_dbu_job,
        temps_overhead_min=temps_overhead_min,
        temps_execucio_min=temps_execucio_per_tasca_min,
        max_parallel_tasks=max_parallel_tasks_job,
        total_tasks=nombre_tasques
    )
    cost_total_job = nombre_tasques * cost_per_tasca_job
    
    # Configuració All-Purpose Cluster
    nodes_all_purpose_driver = 1
    nodes_all_purpose_workers = nombre_workers_all_purpose
    dbus_all_purpose = (nodes_all_purpose_driver + nodes_all_purpose_workers) * instancia_all_purpose.DBUs
    cost_vm_all_purpose_driver = nodes_all_purpose_driver * instancia_all_purpose.cost_per_hour
    cost_vm_all_purpose_workers = nodes_all_purpose_workers * instancia_all_purpose.cost_per_hour
    cost_vm_all_purpose_total = cost_vm_all_purpose_driver + cost_vm_all_purpose_workers
    
    # Càlcul del cost en All-Purpose Cluster
    tasks_per_worker_all_purpose = 1  # Limitar a una tasca per worker
    total_parallel_tasks_all_purpose = nombre_workers_all_purpose * tasks_per_worker_all_purpose
    nombre_onades_all_purpose = ceil(nombre_tasques / total_parallel_tasks_all_purpose)
    temps_execucio_total_min_all_purpose = nombre_onades_all_purpose * temps_execucio_per_tasca_min
    temps_total_actiu_min_all_purpose = temps_overhead_min + temps_execucio_total_min_all_purpose
    
    cost_total_all_purpose, cost_dbu_all_purpose_per_hour, cost_vm_all_purpose_per_hour, cost_total_per_hour_all_purpose = calcular_cost_all_purpose(
        driver_cost_per_hour=cost_vm_all_purpose_driver,
        workers_cost_per_hour=cost_vm_all_purpose_workers,
        total_DBUs=dbus_all_purpose,
        cost_dbu_all_purpose=cost_dbu_all_purpose,
        temps_total_actiu_min=temps_total_actiu_min_all_purpose
    )
    
    # Layout principal amb columnes
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("📈 Resultats Job Cluster")
        
        # Secció de Detalls del Clúster
        with st.expander("📋 Detalls del Job Cluster"):
            st.markdown(f"""
            - **Tipus d'Instància**: {instancia_job.name}
            - **Nombre de Drivers**: {nodes_job_driver}
            - **Nombre de Workers**: {nodes_job_workers}
            - **vCPUs per Node**: {instancia_job.vCPUs}
            - **DBUs per Node**: {instancia_job.DBUs}
            - **RAM per Node**: {instancia_job.RAM_GB} GB
            """)
        
        # Secció de Càlculs de Cost
        with st.expander("💰 Càlculs de Cost Job Cluster"):
            st.markdown(f"""
            **Passos per calcular el cost total en un Job Cluster:**
            
            1. **Nombre d'Etapes (Onades)**:
                - **Fórmula**: Nombre de Tasques / Nombre màxim de Tasques en Paral·lel
                - **Aplicació**: {nombre_tasques} tasques / {max_parallel_tasks_job} tasques = {nombre_onades_job} etapes
            
            2. **Temps Total Actiu per Etapa**:
                - **Fórmula**: Temps d'Execució per Tasca + Temps Overhead
                - **Aplicació**: {temps_execucio_per_tasca_min} minuts + {temps_overhead_min} minuts = {temps_execucio_per_tasca_min + temps_overhead_min} minuts
            
            3. **Temps Total Actiu**:
                - **Fórmula**: Nombre d'Etapes * Temps Total Actiu per Etapa
                - **Aplicació**: {nombre_onades_job} etapes * {temps_execucio_per_tasca_min + temps_overhead_min} minuts = **{temps_total_min_job} minuts**
            
            4. **Cost de les VM durant el Temps Total Actiu**:
                - **Fórmula**: (Temps Total Actiu / 60) * (Cost Driver + Cost Workers)
                - **Aplicació**: ({temps_total_min_job} minuts / 60) * (€{cost_vm_job_driver} + €{cost_vm_job_workers}) = **€{cost_vm_total_job:.4f}**
            
            5. **Cost de les DBUs durant l'Execució**:
                - **Fórmula**: (Temps Execució per Tasca / 60) * Total DBUs * Cost per DBU-hora * Nombre d'Etapes
                - **Aplicació**: ({temps_execucio_per_tasca_min} minuts / 60) * {total_DBUs_job} DBUs * €{cost_dbu_job} per DBU-hora * {nombre_onades_job} etapes = **€{cost_dbu_execucio_job:.4f}**
            
            6. **Cost Total per Tasca**:
                - **Fórmula**: Cost VM Total + Cost DBU Execució
                - **Aplicació**: €{cost_vm_total_job:.4f} + €{cost_dbu_execucio_job:.4f} = **€{cost_per_tasca_job:.4f}**
            
            7. **Cost Total del Job Cluster**:
                - **Fórmula**: Nombre de Tasques * Cost Total per Tasca
                - **Aplicació**: {nombre_tasques} tasques * €{cost_per_tasca_job:.4f} = **€{cost_total_job:.4f}**
            """)
        
        # Metrics per Job Cluster
        st.metric(label="**Cost per tasca**", value=f"€{cost_per_tasca_job:.4f}")
        st.metric(label="**Cost total**", value=f"€{cost_total_job:.4f}")
        st.metric(label="**Temps Total Actiu**", value=f"{temps_total_min_job} minuts")
    
    with col2:
        st.header("📉 Resultats All-Purpose Cluster")
        
        # Secció de Detalls del Clúster
        with st.expander("📋 Detalls de l'All-Purpose Cluster"):
            st.markdown(f"""
            - **Tipus d'Instància**: {instancia_all_purpose.name}
            - **Nombre de Drivers**: {nodes_all_purpose_driver}
            - **Nombre de Workers**: {nodes_all_purpose_workers}
            - **vCPUs per Node**: {instancia_all_purpose.vCPUs}
            - **DBUs per Node**: {instancia_all_purpose.DBUs}
            - **RAM per Node**: {instancia_all_purpose.RAM_GB} GB
            """)
        
        # Secció de Càlculs de Cost
        with st.expander("💰 Càlculs de Cost All-Purpose Cluster"):
            st.markdown(f"""
            **Passos per calcular el cost total en un All-Purpose Cluster:**
            
            1. **Càlcul del Cost de les DBUs per hora**:
                - **Fórmula**: Total DBUs * Cost per DBU-hora
                - **Aplicació**: {dbus_all_purpose} DBUs * €{cost_dbu_all_purpose} per DBU-hora = **€{cost_dbu_all_purpose_per_hour:.4f} €/h**
            
            2. **Càlcul del Cost de les VM per hora**:
                - **Fórmula**: Cost Driver + Cost Workers
                - **Aplicació**: €{cost_vm_all_purpose_driver} + €{cost_vm_all_purpose_workers} = **€{cost_vm_all_purpose_per_hour:.4f} €/h**
            
            3. **Càlcul del Cost Total per hora All-Purpose**:
                - **Fórmula**: Cost DBU All-Purpose per hora + Cost VM All-Purpose per hora
                - **Aplicació**: €{cost_dbu_all_purpose_per_hour:.4f} €/h + €{cost_vm_all_purpose_per_hour:.4f} €/h = **€{cost_total_per_hour_all_purpose:.4f} €/h**
            
            4. **Càlcul del Cost Total All-Purpose durant l'Actiu**:
                - **Etapes**: {nombre_tasques} tasques / {nombre_workers_all_purpose} workers = {nombre_onades_all_purpose} etapes
                - **Temps total actiu**: {nombre_onades_all_purpose} etapes * {temps_execucio_per_tasca_min} minuts tasca + {temps_overhead_min} minuts overhead = {temps_total_actiu_min_all_purpose} minuts
                
                - **Fórmula**: (Temps Total Actiu / 60) * Cost Total per hora All-Purpose
                - **Aplicació**: ({temps_total_actiu_min_all_purpose} minuts / 60) * €{cost_total_per_hour_all_purpose:.4f} €/h = **€{cost_total_all_purpose:.4f}**
            """)
        
        # Metrics per All-Purpose Cluster
        st.metric(label="**Cost total**", value=f"€{cost_total_all_purpose:.4f}")
        st.metric(label="**Temps Total Actiu**", value=f"{temps_total_actiu_min_all_purpose} minuts")
    
    # Visualització gràfica de comparació de costos
    st.header("📊 Comparació de Costos")
    
    # Dades per al gràfic
    data_cost = pd.DataFrame({
        'Clúster': ['Job Cluster', 'All-Purpose Cluster'],
        'Cost Total (€)': [cost_total_job, cost_total_all_purpose]
    })
    
    # Crear gràfic de barres per costos
    bar_chart_cost = alt.Chart(data_cost).mark_bar().encode(
        x=alt.X('Clúster', sort=None, title='Tipus de Clúster'),
        y=alt.Y('Cost Total (€)', title='Cost Total (€)'),
        color='Clúster'
    ).properties(
        width=600,
        height=400,
        title='Comparació dels Costos Totals'
    )
    
    st.altair_chart(bar_chart_cost, use_container_width=True)
    
    # Visualització gràfica de comparació de temps
    st.header("⏰ Comparació de Temps d'Execució")
    
    # Dades per al gràfic de temps
    data_time = pd.DataFrame({
        'Clúster': ['Job Cluster', 'All-Purpose Cluster'],
        'Temps Total Actiu (minuts)': [temps_total_min_job, temps_total_actiu_min_all_purpose]
    })
    
    # Crear gràfic de barres per temps
    bar_chart_time = alt.Chart(data_time).mark_bar().encode(
        x=alt.X('Clúster', sort=None, title='Tipus de Clúster'),
        y=alt.Y('Temps Total Actiu (minuts)', title='Temps Total Actiu (minuts)'),
        color='Clúster'
    ).properties(
        width=600,
        height=400,
        title='Comparació dels Temps Totals Actius'
    )
    
    st.altair_chart(bar_chart_time, use_container_width=True)
    
    # Feedback Visual addicional: Optimalitat en Temps vs Cost
    st.header("📈 Optimalitat en Temps vs Cost")
    
    # Creació d'un gràfic de dispersió combinant cost i temps
    data_optimal = pd.DataFrame({
        'Clúster': ['Job Cluster', 'All-Purpose Cluster'],
        'Cost Total (€)': [cost_total_job, cost_total_all_purpose],
        'Temps Total Actiu (minuts)': [temps_total_min_job, temps_total_actiu_min_all_purpose]
    })
    
    scatter_chart = alt.Chart(data_optimal).mark_circle(size=100).encode(
        x=alt.X('Cost Total (€)', title='Cost Total (€)'),
        y=alt.Y('Temps Total Actiu (minuts)', title='Temps Total Actiu (minuts)'),
        color='Clúster',
        tooltip=['Clúster', 'Cost Total (€)', 'Temps Total Actiu (minuts)']
    ).properties(
        width=600,
        height=400,
        title='Optimalitat en Temps vs Cost'
    )
    
    st.altair_chart(scatter_chart, use_container_width=True)
    
    # Final Results and Conclusion
    st.header("🏆 Resultats Finals")
    st.write(f"**Cost total Job Clusters:** €{cost_total_job:.4f}")
    st.write(f"**Cost total All-Purpose:** €{cost_total_all_purpose:.4f}")
    st.write(f"**Temps total actiu Job Cluster:** {temps_total_min_job} minuts")
    st.write(f"**Temps total actiu All-Purpose Cluster:** {temps_total_actiu_min_all_purpose} minuts")
    
    diferencia_cost = abs(cost_total_job - cost_total_all_purpose)
    if cost_total_job < cost_total_all_purpose:
        estalvi = diferencia_cost
        percentatge_estalvi = (diferencia_cost / cost_total_all_purpose) * 100
        st.success(f"La opció més econòmica és **Job Clusters**")
        st.write(f"**Estalvi en Cost:** €{estalvi:.4f}")
        st.write(f"**Percentatge d'estalvi en Cost:** {percentatge_estalvi:.2f}%")
    else:
        estalvi = diferencia_cost
        percentatge_estalvi = (diferencia_cost / cost_total_job) * 100
        st.success(f"La opció més econòmica és **All-Purpose**")
        st.write(f"**Estalvi en Cost:** €{estalvi:.4f}")
        st.write(f"**Percentatge d'estalvi en Cost:** {percentatge_estalvi:.2f}%")
    
    # Footer amb informació addicional
    st.markdown("---")
    st.markdown("""
    📝 **Nota**: Aquests càlculs són aproximacions i poden variar segons la naturalesa específica de les tasques, la configuració del clúster i altres factors operatius.
    """)

if __name__ == "__main__":
    main()
