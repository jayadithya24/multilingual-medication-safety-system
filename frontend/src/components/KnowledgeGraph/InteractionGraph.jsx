import KnowledgeGraph from "./KnowledgeGraph";
export default function InteractionGraph({ drug1, drug2 }) {
  return <KnowledgeGraph key={`${drug1}-${drug2}`} drug1={drug1} drug2={drug2} />;
}
