import React, { useState, useEffect, useCallback } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, Alert, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, RefreshControl } from 'react-native';

// 🔴 SEU IP AQUI
const API_URL = 'https://coronaled-sorcerously-ranae.ngrok-free.dev'; 

// Interfaces Tipadas (Contrato com o Backend)
interface PensamentoProps {
  id: string;
  tipo: string;
  conteudo: string;
  created_at: string;
  origem: string;
  confianca?: string;
  status: string;
}

interface EstadoCognitivo {
  score_atual: number;
  nivel_carga: string;
  diagnostico_resumido: string;
}

interface Briefing {
  estado_atual: EstadoCognitivo;
  estrategia_do_momento: string;
  acao_tatica_sugerida: string;
  mensagem_motivacional: string;
}

export default function HomeScreen() {
  const [texto, setTexto] = useState('');
  const [projeto, setProjeto] = useState('shaula_orb');
  const [tipo, setTipo] = useState('Ideia');
  const [confianca, setConfianca] = useState('Media');
  
  // Estado do Briefing (Cérebro da Shaula)
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  
  const [enviando, setEnviando] = useState(false);
  const [contexto, setContexto] = useState<PensamentoProps[]>([]);
  const [loading, setLoading] = useState(false);

  const tiposDisponiveis = ['Ideia', 'Tarefa', 'Referencia', 'Duvida'];
  const niveisConfianca = ['Baixa', 'Media', 'Alta'];

  // --- Lógica de Cores baseada no Score ---
  const getScoreColor = (valor: number) => {
    if (valor >= 80) return '#04D361'; // Verde
    if (valor >= 50) return '#FBA94C'; // Laranja
    return '#FF4C4C'; // Vermelho
  };

  const atualizarTudo = useCallback(async () => {
    setLoading(true);
    try {
      // 1. Busca Contexto (Memória)
      const resContext = await fetch(`${API_URL}/context?projeto=${projeto}&limit=10`);
      const jsonContext = await resContext.json();
      setContexto(jsonContext.itens || []);

      // 2. Busca Briefing (Inteligência) - Substitui o antigo /analysis
      const resBriefing = await fetch(`${API_URL}/briefing`);
      const jsonBriefing = await resBriefing.json();
      setBriefing(jsonBriefing);

    } catch (error) {
      console.log("Erro de conexão");
    } finally {
      setLoading(false);
    }
  }, [projeto]);

  useEffect(() => {
    atualizarTudo();
  }, [atualizarTudo]);

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
          projeto_associado: projeto.trim(),
          confianca: confianca
        })
      });

      if (response.ok) {
        setTexto('');
        atualizarTudo();
      } else {
        Alert.alert("Erro", "Falha ao persistir.");
      }
    } catch (error) {
      Alert.alert("Offline", "Verifique conexão.");
    } finally {
      setEnviando(false);
    }
  };

  const resolverPensamento = async (id: string) => {
    try {
      setContexto(prev => prev.filter(item => item.id !== id));
      const response = await fetch(`${API_URL}/thoughts/${id}/status?status=resolvido`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify('resolvido')
      });
      if (response.ok) {
        setTimeout(atualizarTudo, 500); // Recalcula estratégia
      }
    } catch (error) {
      atualizarTudo();
    }
  };

  // Atalho para cor atual
  const corAtual = briefing ? getScoreColor(briefing.estado_atual.score_atual) : '#8257E5';

  return (
    <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.container}>
      <ScrollView 
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={atualizarTudo} tintColor={corAtual}/>}
      >
        
        {/* HEADER */}
        <View style={styles.header}>
          <View>
            <Text style={styles.titulo}>SHAULA <Text style={styles.versao}>V1.3</Text></Text>
            {briefing && (
              <Text style={[styles.statusLabel, { color: corAtual }]}>
                {briefing.estado_atual.nivel_carga.toUpperCase()}
              </Text>
            )}
          </View>
          <View style={styles.scoreBox}>
            <Text style={[styles.scoreValue, { color: corAtual }]}>
              {briefing?.estado_atual.score_atual || '-'}
            </Text>
            <Text style={styles.scoreLabel}>SCORE</Text>
          </View>
        </View>

        {/* --- CARTÃO DE ESTRATÉGIA (O CÉREBRO) --- */}
        {briefing && (
          <View style={[styles.strategyCard, { borderColor: corAtual }]}>
            <Text style={[styles.strategyTitle, { color: corAtual }]}>
              {briefing.estrategia_do_momento}
            </Text>
            <Text style={styles.strategyAction}>
              {briefing.acao_tatica_sugerida}
            </Text>
            {briefing.mensagem_motivacional && (
               <Text style={styles.strategyQuote}>"{briefing.mensagem_motivacional}"</Text>
            )}
          </View>
        )}

        {/* INPUT CONTEXTO */}
        <View style={styles.section}>
          <TextInput 
            style={styles.inputProj} 
            value={projeto} 
            onChangeText={setProjeto}
            onEndEditing={atualizarTudo} 
          />
        </View>

        {/* INPUT COGNITIVO */}
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

        {/* SELETORES */}
        <View style={styles.row}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {tiposDisponiveis.map((t) => (
              <TouchableOpacity 
                key={t} 
                style={[styles.chip, tipo === t && styles.chipSelected]}
                onPress={() => setTipo(t)}
              >
                <Text style={[styles.chipText, tipo === t && styles.chipTextSelected]}>{t}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        <View style={styles.row}>
          <Text style={styles.miniLabel}>Relevância:</Text>
          {niveisConfianca.map((c) => (
            <TouchableOpacity 
              key={c} 
              style={[
                styles.confChip, 
                confianca === c && styles.confChipSelected,
                confianca === c && c === 'Alta' && { borderColor: '#FF4C4C' }
              ]}
              onPress={() => setConfianca(c)}
            >
              <Text style={[
                styles.confText, 
                confianca === c && styles.confTextSelected,
                confianca === c && c === 'Alta' && { color: '#FF4C4C' }
              ]}>{c}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity style={[styles.botaoEnviar, { backgroundColor: corAtual }]} onPress={capturarPensamento} disabled={enviando}>
          {enviando ? <ActivityIndicator color="#000" /> : <Text style={styles.textoEnviar}>PERSISTIR</Text>}
        </TouchableOpacity>

        {/* LISTA */}
        {contexto.map((item) => (
          <View key={item.id} style={[
              styles.card, 
              { borderLeftColor: item.confianca === 'Alta' ? '#FF4C4C' : item.tipo === 'Duvida' ? '#FBA94C' : '#04D361' }
            ]}>
            <View style={styles.cardContent}>
              <View style={styles.cardMeta}>
                <Text style={styles.cardTipo}>{item.tipo}</Text>
                {item.confianca === 'Alta' && <Text style={styles.tagAlta}>ALTA</Text>}
                <Text style={styles.cardTime}>{new Date(item.created_at).toLocaleDateString()}</Text>
              </View>
              <Text style={styles.cardText}>{item.conteudo}</Text>
            </View>
            <TouchableOpacity style={styles.checkBtn} onPress={() => resolverPensamento(item.id)}>
              <View style={styles.checkCircle}>
                <Text style={styles.checkIcon}>✓</Text>
              </View>
            </TouchableOpacity>
          </View>
        ))}

        <View style={{height: 40}} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#09090A' },
  scroll: { padding: 20, paddingTop: 50 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  titulo: { color: '#E1E1E6', fontSize: 24, fontWeight: 'bold' },
  versao: { color: '#8257E5', fontSize: 16 },
  statusLabel: { fontSize: 12, fontWeight: 'bold', letterSpacing: 1, marginTop: 4 },
  scoreBox: { alignItems: 'flex-end' },
  scoreValue: { fontSize: 32, fontWeight: 'bold' },
  scoreLabel: { color: '#7C7C8A', fontSize: 10, letterSpacing: 1, fontWeight: 'bold' },
  
  // NOVO: CARTÃO DE ESTRATÉGIA
  strategyCard: { backgroundColor: '#121214', padding: 16, borderRadius: 8, marginBottom: 20, borderWidth: 1, borderLeftWidth: 4 },
  strategyTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
  strategyAction: { color: '#E1E1E6', fontSize: 15, lineHeight: 22, marginBottom: 8 },
  strategyQuote: { color: '#7C7C8A', fontSize: 12, fontStyle: 'italic' },

  section: { marginBottom: 15 },
  miniLabel: { color: '#7C7C8A', fontSize: 12, marginRight: 10, alignSelf: 'center' },
  inputProj: { backgroundColor: '#121214', color: '#FFF', borderRadius: 8, padding: 12, borderWidth: 1, borderColor: '#202024', fontSize: 16 },
  inputContainer: { marginBottom: 15 },
  input: { backgroundColor: '#121214', color: '#FFF', borderRadius: 8, padding: 15, fontSize: 16, minHeight: 80, textAlignVertical: 'top', borderWidth: 1, borderColor: '#202024' },
  row: { flexDirection: 'row', marginBottom: 15, alignItems: 'center' },
  chip: { paddingVertical: 6, paddingHorizontal: 16, borderRadius: 20, backgroundColor: '#202024', marginRight: 8, borderWidth: 1, borderColor: '#323238' },
  chipSelected: { backgroundColor: '#29292E', borderColor: '#E1E1E6' },
  chipText: { color: '#C4C4CC', fontSize: 12 },
  chipTextSelected: { color: '#FFF', fontWeight: 'bold' },
  confChip: { paddingVertical: 4, paddingHorizontal: 12, borderRadius: 6, backgroundColor: '#202024', marginRight: 8, borderWidth: 1, borderColor: '#323238' },
  confChipSelected: { backgroundColor: '#29292E', borderColor: '#04D361' },
  confText: { color: '#7C7C8A', fontSize: 10, fontWeight: 'bold' },
  confTextSelected: { color: '#04D361' },
  botaoEnviar: { height: 50, borderRadius: 8, justifyContent: 'center', alignItems: 'center', marginVertical: 10 },
  textoEnviar: { color: '#000', fontWeight: 'bold', fontSize: 16 },
  card: { backgroundColor: '#121214', borderRadius: 8, marginBottom: 10, borderLeftWidth: 4, flexDirection: 'row', overflow: 'hidden' },
  cardContent: { flex: 1, padding: 16 },
  cardMeta: { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
  cardTipo: { color: '#E1E1E6', fontSize: 10, fontWeight: 'bold', marginRight: 8, textTransform: 'uppercase' },
  tagAlta: { color: '#FF4C4C', fontSize: 9, fontWeight: 'bold', marginRight: 8, borderWidth: 1, borderColor: '#FF4C4C', paddingHorizontal: 4, borderRadius: 4 },
  cardTime: { color: '#7C7C8A', fontSize: 10 },
  cardText: { color: '#C4C4CC', fontSize: 14, lineHeight: 20 },
  checkBtn: { width: 50, backgroundColor: '#202024', justifyContent: 'center', alignItems: 'center' },
  checkCircle: { width: 24, height: 24, borderRadius: 12, borderWidth: 2, borderColor: '#323238', justifyContent: 'center', alignItems: 'center' },
  checkIcon: { color: '#04D361', fontSize: 14, fontWeight: 'bold' }
});