from PySide6.QtCore import Qt
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import gene_converter as gene
from io import StringIO
import pandas as pd
import numpy as np
import qdarktheme
from PySide6.QtCore import QThread, Signal, Qt,QTimer
import sys
import os
from qt_gui_util import QTextEditHighlighter
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"

class ConvertThread(QThread):
    update_signal = Signal(str)
    finished = Signal()
    def __init__(self, input_text,convert_df,status_bar,is_output_file,case_sensitive,use_nan,use_qc, parent=None):
        super().__init__(parent)
        self.input_text = input_text 
        self.convert_df=convert_df
        self.status_bar=status_bar
        self.is_output_file=is_output_file
        self.case_sensitive=case_sensitive
        self.use_nan=use_nan
        self.use_qc=use_qc
    def run(self):
        self.status_bar.showMessage("Running ... ")
        unmatch_placeholder=""
        qc_fname=None
        if self.use_nan:
            unmatch_placeholder=np.nan
        if self.use_qc:
            qc_fname="convert_qc.txt"
        filter_df,unknow_ensembl_id=gene.gene_ensembl_lines_to_symbol(self.input_text,self.convert_df,self.case_sensitive,unmatch_placeholder=unmatch_placeholder,qc_file_name=qc_fname)
        
        print(filter_df)
        filter_df=filter_df[filter_df.columns]

        text=filter_df.to_string(index=False)
        #texts=texts.splitlines()[1:]
        #for text in texts:
        #    self.update_signal.emit(text)
        #self.finished.emit()
        new_text = "\n".join(text.splitlines()[1:])
        if self.is_output_file:
            with open('output.txt', 'w') as f:
                f.write(new_text)
            
        self.update_signal.emit(new_text)
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(710, 600)
        self.setWindowTitle('Gene Name Tool v0.0.0 (Ensembl ID to Gene Symbol Converter)')
        self.case_sensitive=False
        self.generate_outputfile=False
        self.use_nan=True
        self.use_qc=True
        menu = self.menuBar()

        about_menu = menu.addMenu("&Help")
        button_action = QAction( "&About", self)
        about_menu.addAction(button_action)
        button_action.triggered.connect(self.onAboutButtonClick)
        self.ref_gene_type=QComboBox()
        self.ref_gene_type.addItems(['Mmusculus',"Hsapiens"])
        self.ref_gene_type.currentIndexChanged.connect(self.selected_changed)
        self.df_mm,self.df_mm2,self.df_mm_name=gene.fetch_mm_dataset()
        self.df_hg,self.df_hg2,self.df_hg_name=gene.fetch_hg_dataset()
        self.df=[self.df_mm,self.df_mm2]
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        layout = QFormLayout(centralWidget)
        layout.setLabelAlignment(Qt.AlignLeft)
        layout.setFormAlignment(Qt.AlignLeft)
        center_layout= QVBoxLayout()

        
        v_widget = QWidget()
        v_widget.setLayout(center_layout)
        v_widget.setFixedWidth(80)

        left_layout = QVBoxLayout()
        self.EnsemblTextEdit = QTextEditHighlighter()
        self.EnsemblTextEdit.setFixedWidth(300)
        left_layout.addWidget(QLabel('Ensembl Gene ID'))
        left_layout.addWidget(self.EnsemblTextEdit )
        right_layout = QVBoxLayout()
        self.GeneSymbolTextEdit = QTextEditHighlighter()
        self.GeneSymbolTextEdit.setFixedWidth(300)
        right_layout.addWidget( QLabel('Gene Symbol'))
        right_layout.addWidget( self.GeneSymbolTextEdit)

        self.EnsemblTextEdit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.GeneSymbolTextEdit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        text_layout = QHBoxLayout()
        text_layout.addLayout(left_layout)
        text_layout.addWidget(v_widget)
        text_layout.addLayout(right_layout)
        text_layout.setStretch(0, 1)
        text_layout.setStretch(1, 1)
        layout.addRow(self.ref_gene_type)
        layout.addRow(text_layout )
        # outputfile checkbox
        self.outputfile_checkbox=QCheckBox()
        self.outputfile_checkbox.setText('Output with a txt file.')
        self.outputfile_checkbox.setChecked(False)
        self.outputfile_checkbox.clicked.connect(self.update_generate_outputfile)
        # case sensitive checkbox
        self.case_sensitive_checkbox=QCheckBox()
        self.case_sensitive_checkbox.setText('Matching input text with case sensitivity')
        self.case_sensitive_checkbox.setChecked(False)
        self.case_sensitive_checkbox.clicked.connect(self.update_case_sensitive)
        # use nan or not checkbox
        self.use_nan_checkbox=QCheckBox()
        self.use_nan_checkbox.setText('use NaN to represent as unmatch inputs')
        self.use_nan_checkbox.setChecked(True)
        self.use_nan_checkbox.clicked.connect(self.update_use_nan)
        #
                # use nan or not checkbox
        self.use_qc_file_checkbox=QCheckBox()
        self.use_qc_file_checkbox.setText('output convert QC file')
        self.use_qc_file_checkbox.setChecked(True)
        self.use_qc_file_checkbox.clicked.connect(self.update_qc_f)
        
        layout.addRow(self.case_sensitive_checkbox)
        layout.addRow(self.outputfile_checkbox)
        layout.addRow(self.use_nan_checkbox)
        layout.addRow(self.use_qc_file_checkbox)
        convertButtonEnsembltoSymbol = QPushButton("⇨")
        #layout.addRow(convertButtonEnsembltoSymbol)
        center_layout.addWidget(convertButtonEnsembltoSymbol)
        convertButtonSymboltoEnsembl = QPushButton("⇦")#Symbol to Ensembl ID
        #layout.addRow(convertButtonSymboltoEnsembl)
        center_layout.addWidget(convertButtonSymboltoEnsembl)
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        
        convertButtonEnsembltoSymbol.clicked.connect(self.convert_ensemblid_to_symbol)
        convertButtonSymboltoEnsembl.clicked.connect(self.convert_symbol_to_ensemblid)

    def update_result(self, new_text):
        previous_text=self.GeneSymbolTextEdit.toPlainText()
        if previous_text!="":
            self.GeneSymbolTextEdit.setPlainText(previous_text+"\n"+new_text)
        else:
            self.GeneSymbolTextEdit.setPlainText(new_text)
        
    def update_result2(self, new_text):
        previous_text=  self.EnsemblTextEdit.toPlainText()
        if previous_text!="":
            self.EnsemblTextEdit.setPlainText(previous_text+"\n"+new_text)
        else:
            self.EnsemblTextEdit.setPlainText(new_text)
        
    def selected_changed(self,index):
        if self.ref_gene_type.currentText()=='Mmusculus':
            self.df[0]=self.df_mm
            self.df[1]=self.df_mm2
        elif  self.ref_gene_type.currentText()=='Hsapiens':
            self.df[0]=self.df_hg
            self.df[1]=self.df_hg2
        else:
            raise ValueError("unknow ref_gene_type ")
    def update_case_sensitive(self):
        self.case_sensitive =self.case_sensitive_checkbox.isChecked()  
    
    def update_generate_outputfile(self):
        self.generate_outputfile=self.outputfile_checkbox.isChecked()
    
    def update_use_nan(self):
        self.use_nan =self.use_nan_checkbox.isChecked()  
    
    def update_qc_f(self):
        self.use_qc =self.use_qc_file_checkbox.isChecked()  
        print(self.use_qc)
        
    def update_generate_outputfile(self):
        self.generate_outputfile=self.outputfile_checkbox.isChecked()
    def convert_ensemblid_to_symbol(self):
        self.GeneSymbolTextEdit.setPlainText("")
        input_text = self.EnsemblTextEdit.toPlainText()
        self.convert_thread = ConvertThread(input_text=input_text,convert_df=self.df[0],status_bar=self.status_bar,is_output_file=self.generate_outputfile,case_sensitive=self.case_sensitive,use_nan=self.use_nan,use_qc=self.use_qc)
        self.convert_thread.update_signal.connect(self.update_result)
        self.convert_thread.start()
        self.convert_thread.finished.connect(self.on_task_finished)

    def convert_symbol_to_ensemblid(self):

        self.EnsemblTextEdit.setPlainText("")
        input_text = self.GeneSymbolTextEdit.toPlainText()
        self.convert_thread = ConvertThread(input_text=input_text,convert_df=self.df[1],status_bar=self.status_bar,is_output_file=self.generate_outputfile,case_sensitive=self.case_sensitive,use_nan=self.use_nan,use_qc=self.use_qc)
        self.convert_thread.update_signal.connect(self.update_result2)
        self.convert_thread.start()
        self.convert_thread.finished.connect(self.on_task_finished)

        
    def on_task_finished(self):

        self.status_bar.showMessage("Finish converting .")
        QTimer.singleShot(1000,self.clear_status_bar )

    def clear_status_bar(self):
        self.status_bar.showMessage("")

    def closeEvent(self, event):
        super().closeEvent(event)
        os._exit(0)
    def onAboutButtonClick(self,event):
        msgBox = QMessageBox()
        msgBox.setWindowTitle("About ")
        msgBox.setText("Gene Name Tool v0.0.0 \nauthor: YMH")
        msgBox.exec()
        
if __name__ == "__main__":

    qdarktheme.enable_hi_dpi()
    app = QApplication(sys.argv)
    qdarktheme.setup_theme(custom_colors={"primary": "#d9d9d9"})
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
    os._exit(0)
