# pFillGaps
# Copyright (C) [2024] [Cláudio Bielenki Jr]
#
# Este programa é software livre; você pode redistribuí-lo e/ou
# modificá-lo sob os termos da Licença Pública Geral GNU,
# conforme publicada pela Free Software Foundation; tanto a versão 3
# da Licença, ou (a seu critério) qualquer versão posterior.
#
# Este programa é distribuído na esperança de que seja útil,
# mas SEM NENHUMA GARANTIA; nem mesmo a garantia implícita de
# COMERCIABILIDADE OU ADEQUAÇÃO A UM PROPÓSITO ESPECÍFICO. Consulte a
# Licença Pública Geral GNU para mais detalhes.
#
# Você deve ter recebido uma cópia da Licença Pública Geral GNU
# junto com este programa; se não, veja <https://www.gnu.org/licenses/>.

import numpy as np
from pathlib import Path
import pandas as pd
from PyQt5.QtGui import QColor
import geopandas as gpd
from pyproj import CRS
from pyproj.database import query_utm_crs_info
from pyproj.aoi import AreaOfInterest
import sys, os
from osgeo import ogr
from PyQt5 import uic
from PyQt5.QtWidgets import QFileDialog, QSizePolicy, QToolBar
from resources_rc import *
from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from FillGapDialog import pFillGapDialog
from creditoDialog import creditoDialog
if getattr(sys, 'frozen', False):
    # Define PROJ_LIB para o diretório onde o proj.db foi incluído no .spec
    os.environ['PROJ_LIB'] = os.path.join(sys._MEIPASS, 'proj')
    # Define GDAL_DATA para o diretório onde os dados do GDAL foram incluídos no .spec
    os.environ['GDAL_DATA'] = os.path.join(sys._MEIPASS, 'gdal')

# Subclasse de QAbstractTableModel para usar o DataFrame
class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super(PandasModel, self).__init__()
        self._data = data
        # Armazena as localizações das células originalmente NaN
        self._nan_locations = data.isna()

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        value = self._data.iat[index.row(), index.column()]
        # Centralizar o texto na célula
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        # Exibir o valor formatado em três casas decimais, se for um número
        if role == Qt.DisplayRole:
            if isinstance(value, (int, float)):
                return f"{value:.3f}"  # Formata para 3 casas decimais
            return str(value)  # Exibe outros valores como strings
        # Exibir o valor em formato de string
        if role == Qt.DisplayRole:
            return str(value)
        # Verificar a localização original de NaN e aplicar destaque
        if role == Qt.BackgroundRole and self._nan_locations.iat[index.row(), index.column()]:
            return QColor(140, 200, 255)  # Azul claro para células originalmente NaN
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            elif orientation == Qt.Vertical:
                return str(self._data.index[section])
        return None

    def update_data(self, new_data):
        """Atualiza os dados do modelo e mantém as localizações originais de NaN"""
        self.beginResetModel()
        self._data = new_data
        # Mantém as localizações originais de NaN
        # Não altere `self._nan_locations` para que o destaque seja preservado
        self.endResetModel()

class pyFillGaps(QMainWindow):
    def __init__(self):
        super(pyFillGaps, self).__init__()
        self.preenchimento = None
        self.arrayDist1 = None
        self.dlg = None
        self.arrayDist = None
        self.invMatrixDist = None
        self.matrixDist1 = None
        self.matrixDist = None
        self.arrayCorr = None
        self.matrixCorr = None
        self.columns = None
        self.stds = None
        self.means = None
        self.indexLista = None
        self.gagePlu = None
        self.rows = None
        self.indexSHP = None
        self.indexData = None
        self.maxEst = None
        self.field_names = None
        self.shapefile = None
        self.model = None
        self.colNames = None
        self.dataPlu = None
        self.fileCSV = None
        self.arquivoCSV = None
        self.distancia = None
        uic.loadUi("mainFillGaps.ui", self)  # Replace with your .ui file path
        self.toolbar = self.findChild(QToolBar, "toolBar")
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Expande para preencher o espaço
        self.toolbar.addWidget(spacer)
        self.toolbar.addAction(self.actionCreditos)
        self.appDir = os.path.dirname(__file__)
        self.actionCSV.triggered.connect(self.openCSV)
        self.actionSHP.triggered.connect(self.openSHP)
        self.actionFalhas.triggered.connect(self.pFalhas)
        self.actionSalvarCSV.triggered.connect(self.salvarCSV)
        self.actionCreditos.triggered.connect(self.creditos)
        self.actionSHP.setEnabled(False)
        self.actionFalhas.setEnabled(False)
        self.actionSalvarCSV.setEnabled(False)

    def limpar(self):
        self.preenchimento = None
        self.arrayDist1 = None
        self.dlg = None
        self.arrayDist = None
        self.invMatrixDist = None
        self.matrixDist1 = None
        self.matrixDist = None
        self.arrayCorr = None
        self.matrixCorr = None
        self.columns = None
        self.stds = None
        self.means = None
        self.indexLista = None
        self.gagePlu = None
        self.rows = None
        self.indexSHP = None
        self.indexData = None
        self.maxEst = None
        self.field_names = None
        self.shapefile = None
        self.model = None
        self.colNames = None
        self.dataPlu = None
        self.fileCSV = None
        self.arquivoCSV = None
        self.distancia = None
        self.tableView.setModel(self.model)
        self.actionSHP.setEnabled(False)
        self.actionFalhas.setEnabled(False)
        self.actionSalvarCSV.setEnabled(False)

    def creditos(self):
        self.dlgCreditos = creditoDialog()
        self.dlgCreditos.show()
        result = self.dlgCreditos.exec_()
        if result:
            pass
    def openCSV(self):
        self.arquivoCSV = QFileDialog.getOpenFileName(self, "Select Rainfall Data File Input: ",
                                                         self.appDir, "*.csv")
        self.fileCSV = self.arquivoCSV[0]
        self.dataPlu = pd.read_csv(self.fileCSV)
        self.colNames = list(self.dataPlu.columns)
        self.model = PandasModel(self.dataPlu)
        self.tableView.setModel(self.model)
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.tableView)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.actionSHP.setEnabled(True)
        print(self.colNames)
        pass

    def openSHP(self):
        # Abre o diálogo para selecionar o shapefile
        arquivoSHP, _ = QFileDialog.getOpenFileName(self, "Select Rainfall Gage File Input:", self.appDir, "*.shp")
        print("teste 1 passou")
        # Verifica se um arquivo foi selecionado
        if not arquivoSHP:
            print("Nenhum arquivo selecionado.")
            return  # Sai da função se a seleção foi cancelada
        self.shapefile = arquivoSHP  # Atribui o caminho do shapefile selecionado
        self.field_names = []  # Inicializa a lista de nomes de campos
        print("teste 2 passou")
        # Verifica se o arquivo existe
        if not os.path.exists(self.shapefile):
            print(f"Erro: O arquivo {self.shapefile} não foi encontrado.")
            return
        # Carrega o driver do shapefile
        driver = ogr.GetDriverByName('ESRI Shapefile')
        if driver is None:
            print("Erro: Driver 'ESRI Shapefile' não encontrado.")
            return
        print(self.shapefile)
        print("teste 3 passou")
        # Abre o shapefile
        datasource = driver.Open(self.shapefile, 0)  # 0 para leitura
        if datasource is None:
            print("Erro: não foi possível abrir o shapefile.")
            return
        print("teste 4 passou")
        # Verifica se o datasource foi carregado com sucesso
        if datasource is None:
            print("Erro: não foi possível abrir o shapefile.")
            return
        print("teste 5 passou")
        # Obtém a camada (layer) do shapefile
        shapefile_layer = datasource.GetLayer()
        if shapefile_layer:
            print("shapefile_layer carregado com sucesso.")
            layer_def = shapefile_layer.GetLayerDefn()
            if layer_def is not None:
                print("Obtendo nomes dos campos de atributos...")
                for i in range(layer_def.GetFieldCount()):
                    name = layer_def.GetFieldDefn(i).GetName()
                    print(f"Campo: {name}")
                    self.field_names.append(name)
            else:
                print("Erro: Não foi possível obter a definição da camada (layer_def).")
        else:
            print("Erro: shapefile_layer não foi carregado.")
        print("teste 6 passou")
        self.actionFalhas.setEnabled(True)
        print(self.field_names)
        print(self.fileCSV)
        print(self.shapefile)

    def on_sliderDist_value_changed(self, value):
        self.distancia = value
        self.dlg.labelDist.setText(str(value))

    def on_sliderGages_value_changed(self, value):
        self.maxEst = value
        self.dlg.labelGage.setText(str(value))

    def upDate(self):
        self.dlg.pbUpDate.setEnabled(False)
        self.distancia = 0
        self.maxEst = 1
        self.indexData = self.dlg.comboBoxDate.currentText()
        self.indexSHP = self.dlg.comboBoxCode.currentText()
        self.dataPlu.set_index(self.indexData, inplace=True)
        self.gagePlu = gpd.read_file(self.shapefile)
        self.gagePlu.set_index(self.indexSHP)
        print("teste 1")
        self.indexLista = self.dataPlu.index.values.tolist()
        srid = CRS(self.gagePlu.crs)
        print("teste 2")
        if srid.coordinate_system.name == 'ellipsoidal':
            extent = self.gagePlu.total_bounds
            utm_crs_list = query_utm_crs_info(datum_name="WGS 84",
                                              area_of_interest=AreaOfInterest(west_lon_degree=extent[0],
                                                                              south_lat_degree=extent[1],
                                                                              east_lon_degree=extent[2],
                                                                              north_lat_degree=extent[3], ), )
            utm_crs = CRS.from_epsg(utm_crs_list[0].code)
            self.gagePlu = self.gagePlu.to_crs(utm_crs)
        self.means = self.dataPlu.mean()
        self.stds = self.dataPlu.std()
        # colNames = list(dataPlu.columns)
        self.rows, self.columns = self.dataPlu.shape
        self.matrixCorr = self.dataPlu.corr()
        self.arrayCorr = self.matrixCorr.to_numpy(dtype=float)
        self.matrixDist = self.gagePlu.geometry.apply(lambda g: (self.gagePlu.distance(g)))
        # Converte para array NumPy se não estiver
        self.matrixDist1 = self.matrixDist.to_numpy(dtype=float)
        # Encontra o valor máximo
        maxDist = int(np.ceil((np.max(self.matrixDist1)) / 1000) * 1000)
        self.dlg.labelDistMax.setText(str(maxDist))
        self.dlg.sliderDist.setEnabled(True)
        self.dlg.sliderDist.setMinimum(0)  # Valor mínimo do slider
        self.dlg.sliderDist.setMaximum(maxDist)  # Valor máximo do slider
        self.dlg.sliderDist.setValue(0)
        self.dlg.sliderDist.valueChanged.connect(self.on_sliderDist_value_changed)
        self.dlg.labelGageMax.setText(str(self.columns))
        self.dlg.sliderGages.setEnabled(True)
        self.dlg.sliderGages.setMinimum(1)  # Valor mínimo do slider
        self.dlg.sliderGages.setMaximum(self.columns)  # Valor máximo do slider
        self.dlg.sliderGages.setValue(1)
        self.dlg.sliderGages.valueChanged.connect(self.on_sliderGages_value_changed)
        self.dlg.method.setEnabled(True)

    def pFalhas(self):
        self.dlg = pFillGapDialog()
        self.dlg.show()
        textName1 = str(Path(self.fileCSV).name)
        print(textName1)
        self.dlg.pathRainfallData.setText(textName1)
        for name in self.colNames:
            self.dlg.comboBoxDate.addItem(name)
        textName = str(Path(self.shapefile).name)
        print(textName)
        self.dlg.pathGageData.setText(textName)
        for field in self.field_names:
            self.dlg.comboBoxCode.addItem(field)
        self.dlg.pbUpDate.clicked.connect(self.upDate)
        result = self.dlg.exec_()
        if result:
            if self.dlg.rbRPM.isChecked():
                method = "Mean"
            if self.dlg.rbRPC.isChecked():
                method = "Correlation"
            if self.dlg.rbIDW.isChecked():
                method = "InvDist"
            self.matrixDist1 = np.where((self.matrixDist1 > self.distancia), 0, 1)
            self.invMatrixDist = 1 / self.matrixDist
            self.arrayDist1 = self.invMatrixDist.to_numpy(dtype=float)
            self.arrayDist = np.multiply(self.arrayDist1, self.matrixDist1)
            for col in range(self.columns):
                for row in range(self.rows):
                    if col == row:
                        self.invMatrixDist[col][row] = 0
            arrayIndices = np.multiply(self.arrayCorr, self.arrayDist)
            #arrayIndices = matrixIndices.to_numpy()
            arrayData = self.dataPlu.to_numpy(dtype=float)
            arrayDataP = np.copy(arrayData)
            arrayPosition = []
            self.preenchimento = {}
            for col in range(self.columns):
                pMeans = self.means[col]
                pStds = self.stds[col]
                for row in range(self.rows):
                    if np.isnan(arrayData[row, col]):
                        chavePreencimento = (self.indexLista[row], self.colNames[col+1])
                        estPreenchimento = []
                        arrayPIndicesCopy = np.empty(shape=self.columns)
                        rowData = np.empty(shape=self.columns)
                        arrayPMedia = np.empty(shape=self.columns)
                        arrayPStds = np.empty(shape=self.columns)
                        arrayPCorr = np.empty(shape=self.columns)
                        arrayPIndices = np.empty(shape=self.columns)
                        arrayPDist = np.empty(shape=self.columns)
                        arraySortIndices = np.empty(shape=self.columns)
                        precX = 0
                        for i in range(self.columns):
                            if not np.isnan(arrayData[row, i]):
                                rowData[i] = arrayData[row, i]
                                arrayPMedia[i] = self.means[i]
                                arrayPStds[i] = self.stds[i]
                                arrayPCorr[i] = self.arrayCorr[col, i]
                                arrayPIndices[i] = arrayIndices[col, i]
                                arrayPDist[i] = self.arrayDist[col, i]
                            else:
                                rowData[i] = 0
                                arrayPMedia[i] = 0
                                arrayPStds[i] = 0
                                arrayPCorr[i] = 0
                                arrayPIndices[i] = 0
                                arrayPDist[i] = 0
                        arrayPIndicesCopy = np.copy(arrayPIndices)
                        arraySortIndices = np.sort(arrayPIndicesCopy)
                        countNZeros = np.count_nonzero(~np.isnan(arraySortIndices) & (arraySortIndices != 0))
                        if countNZeros == 0:
                            estPreenchimento.append("Não preenchido")
                            self.preenchimento[chavePreencimento] = estPreenchimento
                            del rowData
                            del arrayPMedia
                            del arrayPStds
                            del arrayPCorr
                            del arrayPIndices
                            del arrayPIndicesCopy
                            del arraySortIndices
                            continue
                        estValidas = min(self.maxEst, countNZeros)
                        arraySelecao = np.empty(shape=estValidas)
                        Cont = 0
                        for valor in arraySortIndices:
                            if valor > 0 and Cont < estValidas - 1:
                                Cont = Cont + 1
                                arraySelecao[Cont] = valor
                        arraySelecao = arraySortIndices[-(estValidas):]
                        # print(arraySelecao)
                        arrayPos = []
                        for item in arraySelecao:
                            position = np.where(arrayPIndices == item)[0][0]
                            estPreenchimento.append(self.colNames[position+1])
                            if method == "Mean":
                                precX = precX + ((1 / estValidas) * ((pMeans / arrayPMedia[position]) * rowData[position]))
                            if method == "Correlation":
                                precX = precX + ((pStds / estValidas) * (
                                            ((rowData[position] - arrayPMedia[position]) / arrayPStds[position]) *
                                            arrayPCorr[position]))
                            if method == "InvDist":
                                somaDist = 0
                                for item2 in arraySelecao:
                                    position2 = np.where(arrayPIndicesCopy == item2)[0][0]
                                    somaDist = somaDist + arrayPDist[position2]
                                precX = precX + ((arrayPDist[position] / somaDist) * rowData[position])
                        if method == "Mean":
                            arrayDataP[row, col] = precX
                        if method == "Correlation":
                            arrayDataP[row, col] = precX + pMeans
                        if method == "InvDist":
                            arrayDataP[row, col] = precX
                        self.preenchimento[chavePreencimento] = estPreenchimento
                        del rowData
                        del arrayPMedia
                        del arrayPStds
                        del arrayPCorr
                        del arrayPIndices
                        del arrayPIndicesCopy
                        del arraySortIndices
                        del arraySelecao
            #newName = "_Fill_" + method + ".csv"
            # Converte indexList para um DataFrame
            index_df = pd.DataFrame(self.indexLista, columns=[self.colNames[0]])
            # Converte arrayDataP diretamente para um DataFrame com as colunas apropriadas
            data_df = pd.DataFrame(arrayDataP, columns=self.colNames[1:])
            # Concatena os dois DataFrames ao longo das colunas
            self.df = pd.concat([index_df, data_df], axis=1)
            # Define a coluna de índice sem removê-la
            #df.set_index(self.colNames[0], inplace=True, drop=False)
            #df = pd.DataFrame(data_with_index, columns=self.colNames)
            self.model.update_data(self.df)
            self.actionSalvarCSV.setEnabled(True)
        pass

    def salvarCSV(self):
        directory = Path(self.fileCSV).parent
        file_path, _ = QFileDialog.getSaveFileName(
            parent=self,  # Define o widget pai, geralmente `self`
            caption="Salvar arquivo como CSV",  # Título da caixa de diálogo
            directory=str(directory),  # Diretório inicial e sugestão de nome
            filter="CSV Files (*.csv);",  # Filtros de arquivos
            options=QFileDialog.Options()  # Opções adicionais
        )
        # Verifica se o usuário escolheu um arquivo
        if file_path:
            print("Arquivo escolhido:", file_path)
        else:
            print("Nenhum arquivo foi escolhido.")
        self.df.to_csv(file_path)
        # Nome do arquivo onde os dados serão gravados
        log_path = Path(file_path).with_suffix(".log")
        arquivo_log = log_path
        # Abrindo o arquivo em modo de escrita
        with open(arquivo_log, "w") as file:
            # Iterando sobre o dicionário e gravando cada item
            for (data, codigo_estacao), estacoes_usadas in self.preenchimento.items():
                # Formata a linha a ser escrita
                linha = f"{data}, {codigo_estacao}: {', '.join(estacoes_usadas)}\n"
                # Escreve a linha no arquivo
                file.write(linha)
        print(f"Dados gravados com sucesso em {arquivo_log}.")
        self.limpar()
        pass

app = QApplication(sys.argv)
window = pyFillGaps()
window.show()
window.creditos()
sys.exit(app.exec_())