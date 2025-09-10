from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import torch
import random


# Let's create the agent that works with RAG

class LunarTechRAGagent:
    def __init__(self, faq_data, gemma_model = None, gemma_tokenizer = None, threshhold = 0.6):
        self.embeddings = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.faq_data = faq_data['faq']
        self.gemma_model = gemma_model
        self.gemma_tokenizer = gemma_tokenizer
        self.confidence_threshhold = threshhold
        self.faq_embeddings = None

# Create embeddings for all FAQ entries
    def prepare_embeddings(self):

        self.faq_texts = []
        self.faq_entries = []

        for faq in self.faq_data:
            #combined_text = f"Question: {faq['question']} Answer: {faq['answer']} Category: {faq['category']}"
            # combined_text = faq['question']
            combined_text = f"{faq['question']} (Category: {faq['category']})"
            self.faq_texts.append(combined_text)
            self.faq_entries.append(faq)
        self.faq_embeddings = self.embeddings.encode(self.faq_texts)

# Checking the similarity of the question embeddings with the FAQ embeddings with cosine similarity
    def retrieve_relevant_faqs(self, user_question: str, top_k: int = 3):
        if self.faq_embeddings is None:
            self.prepare_embeddings()
        question_embedding = self.embeddings.encode([user_question])
        similarity = cosine_similarity(question_embedding, self.faq_embeddings)[0]

        # top-k most similar FAQs
        top_indices = np.argsort(similarity)[::-1][:top_k]
        relevant_faqs = []
        for idx in top_indices:
            relevant_faqs.append({
                'faq': self.faq_entries[idx],
                'similarity': float(similarity[idx]),
                'index': int(idx)
            })
        
        return relevant_faqs 

    def assess_confidence(self, relevant_faqs, user_question):
        if not relevant_faqs:
            return 0.0

        # Highest similarity score
        max_similarity = max(faq['similarity'] for faq in relevant_faqs)
        
        # Boost confidence if multiple FAQs are relevant
        high_similarity_count = sum(1 for faq in relevant_faqs if faq['similarity'] > 0.6)
        
        # We are a little more confident when there are more than one matching questions (in this case +0.1)
        confidence = max_similarity
        if high_similarity_count > 1:
            confidence = min(1.0, confidence + 0.1)  # Small boost for multiple matches
        
        return confidence

    def _fallback_response(self, relevant_faqs):
        if not relevant_faqs:
            return "No information about that topic."
        
        best_faq = relevant_faqs[0]['faq']
        return best_faq['answer']

    def generate_response_with_gemma(self, user_question, relevant_faqs):
        
        context_parts = []
        for faq_item in relevant_faqs: 
            faq = faq_item['faq']
            
            context_parts.append(faq['answer'])
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""Answer this question:

Question: {user_question}
Context: {context}
Answer:"""
        try:

            inputs = self.gemma_tokenizer(
            prompt, 
            return_tensors="pt", 
            truncation=True, 
            max_length=800
        )
    
            with torch.no_grad():
                outputs = self.gemma_model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.7,  
                    top_p=0.95,       
                    top_k=50,        
                    do_sample=True,
                    pad_token_id=self.gemma_tokenizer.eos_token_id,
                    eos_token_id=self.gemma_tokenizer.eos_token_id
                )
            full_response = self.gemma_tokenizer.decode(outputs[0], skip_special_tokens=True)

            if "Answer:" in full_response:
                generated_response = full_response.split("Answer:")[-1].strip()
            else:
                generated_response = full_response[len(prompt):].strip()
            
            return generated_response

        except Exception as e:
            print(f"Error while generating with Gemma: {e}")
            return self._fallback_response(relevant_faqs)
    
    

    def _generate_escalation_response(self):
        escalation_responses = [
            "I apologize, but I don't have enough specific information to answer your question confidently. Let me connect you with one of our admissions advisors who can provide you with detailed, personalized guidance. Would you like me to arrange that?",
            
            "That's a great question! While I don't have the exact details you're looking for in my current knowledge base, our admissions team would be delighted to give you comprehensive information. Can I help you schedule a brief call with them?",
                    
            "I appreciate your question! To ensure you receive the most current and detailed information, I'd recommend speaking directly with our admissions team. They can provide personalized guidance and answer any specific concerns you might have."
        ]

        return random.choice(escalation_responses)     

    def answer_question(self, user_question):
        
        print(f"Processing question: {user_question}")
        
        relevant_faqs = self.retrieve_relevant_faqs(user_question, top_k=3)
        
        confidence = self.assess_confidence(relevant_faqs, user_question)
        
        print(f"Confidence score: {confidence:.2f}")
        print(f"Found {len(relevant_faqs)} relevant FAQs")
        
        if confidence > 0.8:
            best_faq = relevant_faqs[0]['faq']
            return {
                "answer": best_faq['answer'],
                "confidence": confidence,
            }

        if confidence < self.confidence_threshhold:
            return {
                "answer": self._generate_escalation_response(),
                "confidence": confidence,
            }
        else:
            answer = self.generate_response_with_gemma(user_question, relevant_faqs)
            
            return {
                "answer": answer,
                "confidence": confidence,
            }

