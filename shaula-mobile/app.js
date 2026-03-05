// App.js Atualizado - Fase 2 Engenharia
import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, Alert, ActivityIndicator, KeyboardAvoidingView, Platform, FlatList, ScrollView } from 'react-native';

const API_URL = 'https://coronaled-sorcerously-ranae.ngrok-free.dev'; // 🔴 SEU IP AQUI

export default function App() {
  const [texto, setTexto] = useState('');
  const [projeto, setProjeto] = useState('shaula_orb'); // Default, mas editável
  const [tipo, setTipo] = useState('Ideia');
  const [enviando, setEnviando] = useState(false);
  const [contexto, setContexto] = useState([]); // Memória recuperada
  const [loadingContexto, setLoadingContexto] = useState(false);

  const tiposDisponiveis = ['Ideia', 'Tarefa', 'Referencia', 'Duvida'];

  // 1. Captura (Escrever)
  const capturarPensamento = async () => {
    if (!texto.trim()) return;
    setEnviando(true);
    try {
      const response = await fetch(`${API_URL}/capture`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tipo: tipo,
          conteudo: texto,
          origem: 'mobile',
          projeto_associado: projeto.trim()
        })
      });
      if (response.ok) {
        Alert.alert("✅ Sucesso", "Memória persistida.");
        setTexto('');
        recuperarContexto(); // Já atualiza a lista automaticamente
      } else {
        Alert.alert("Erro", "Falha no núcleo.");
      }
    } catch (error) {
      Alert.alert("Offline", "Não foi possível conectar ao servidor.");
    } finally {
      setEnviando(false);
    }
  };

  // 2. Recuperação (Ler e Atualizar Relevância)
  const recuperarContexto = async () => {
    setLoadingContexto(true);
    try {
      const response = await fetch(`${API_URL}/context?projeto=${projeto}&limit=5`);
      const json = await response.json();
      setContexto(json.itens || []);
    } catch (error) {
      console.log("Erro ao recuperar contexto");
    } finally {
      setLoadingContexto(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        
        <View style={styles.header}>
          <Text style={styles.titulo}>SHAULA <Text style={styles.subtitulo}>V1</Text></Text>
          <View style={styles.healthTag}><Text style={styles.healthText}>ONLINE</Text></View>
        </View>

        {/* Configuração de Contexto */}
        <View style={styles.projContainer}>
          <Text style={styles.label}>Projeto Ativo:</Text>
          <TextInput 
            style={styles.inputProj} 
            value={projeto} 
            onChangeText={setProjeto}
            placeholder="Nome do projeto..."
          />
        </View>

        {/* Área de Input */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder="Input cognitivo..."
            placeholderTextColor="#666"
            multiline
            value={texto}
            onChangeText={setTexto}
          />
        </View>

        <View style={styles.botoesContainer}>
          {tiposDisponiveis.map((t) => (
            <TouchableOpacity 
              key={t} 
              style={[styles.botaoTipo, tipo === t && styles.botaoTipoSelecionado]}
              onPress={() => setTipo(t)}
            >
              <Text style={[styles.textoTipo, tipo === t && styles.textoTipoSelecionado]}>{t}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity style={styles.botaoEnviar} onPress={capturarPensamento} disabled={enviando}>
          {enviando ? <ActivityIndicator color="#FFF" /> : <Text style={styles.textoEnviar}>PERSISTIR</Text>}
        </TouchableOpacity>

        {/* Área de Contexto (Memória Recente) */}
        <View style={styles.contextoHeader}>
          <Text style={styles.label}>Contexto Recente ({projeto})</Text>
          <TouchableOpacity onPress={recuperarContexto}>
            <Text style={styles.refreshText}>🔄 Atualizar</Text>
          </TouchableOpacity>
        </View>

        {loadingContexto ? <ActivityIndicator color="#8257E5" /> : (
          contexto.map((item) => (
            <View key={item.id} style={styles.cardContexto}>
              <View style={styles.cardTop}>
                <Text style={styles.cardTipo}>{item.tipo}</Text>
                <Text style={styles.cardData}>{new Date(item.created_at).toLocaleTimeString()}</Text>
              </View>
              <Text style={styles.cardConteudo}>{item.conteudo}</Text>
            </View>
          ))
        )}
      
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121214' },
  scroll: { padding: 20, paddingTop: 60 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  titulo: { color: '#FFF', fontSize: 28, fontWeight: 'bold' },
  subtitulo: { color: '#8257E5' },
  healthTag: { backgroundColor: '#04D361', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  healthText: { color: '#000', fontSize: 10, fontWeight: 'bold' },
  
  projContainer: { marginBottom: 15 },
  label: { color: '#E1E1E6', marginBottom: 5, fontSize: 14, fontWeight: 'bold' },
  inputProj: { backgroundColor: '#202024', color: '#FFF', borderRadius: 6, padding: 10, borderWidth: 1, borderColor: '#29292E' },

  inputContainer: { marginBottom: 15 },
  input: { backgroundColor: '#202024', color: '#FFF', borderRadius: 6, padding: 15, fontSize: 16, height: 80, textAlignVertical: 'top' },
  
  botoesContainer: { flexDirection: 'row', gap: 8, marginBottom: 20 },
  botaoTipo: { paddingVertical: 6, paddingHorizontal: 12, borderRadius: 20, borderWidth: 1, borderColor: '#29292E' },
  botaoTipoSelecionado: { backgroundColor: '#8257E5', borderColor: '#8257E5' },
  textoTipo: { color: '#E1E1E6', fontSize: 12 },
  textoTipoSelecionado: { color: '#FFF', fontWeight: 'bold' },
  
  botaoEnviar: { backgroundColor: '#8257E5', height: 50, borderRadius: 6, justifyContent: 'center', alignItems: 'center', marginBottom: 30 },
  textoEnviar: { color: '#FFF', fontWeight: 'bold' },

  contextoHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10, borderTopWidth: 1, borderTopColor: '#29292E', paddingTop: 20 },
  refreshText: { color: '#8257E5', fontSize: 14 },
  
  cardContexto: { backgroundColor: '#202024', padding: 12, borderRadius: 6, marginBottom: 10, borderLeftWidth: 3, borderLeftColor: '#04D361' },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 5 },
  cardTipo: { color: '#04D361', fontSize: 12, fontWeight: 'bold', textTransform: 'uppercase' },
  cardData: { color: '#666', fontSize: 10 },
  cardConteudo: { color: '#E1E1E6', fontSize: 14 }
});