# Deep Dive: AI/ML Foundations for RAG & Beyond

**Purpose:** Comprehensive understanding of AI/ML fundamentals  
**Approach:** Bottom-up, theory-first with practical examples  
**Style:** Concise, no boilerplate, with apt analogies

---

## Learning Path Structure

This document is organized in dependency order - each section builds on previous ones.

**Estimated Timeline:** 4-6 weeks for solid foundation (2-3 hours/day)

---

## Part 1: Mathematical Foundations (Week 1)

### 1.1 Linear Algebra (The Language of ML)

**Why it matters:** Everything in ML is vectors and matrices.

#### Core Concepts

**Vectors**
- Geometric: Direction + magnitude in n-dimensional space
- Algebraic: Ordered list of numbers `[x₁, x₂, ..., xₙ]`
- **In ML:** Data points, embeddings, weights

**Matrices**
- 2D arrays of numbers
- **In ML:** Transformations, weight matrices in neural networks
- Operations: multiplication, transpose, inverse

**Vector Operations:**
- **Dot product:** `a·b = Σ aᵢbᵢ` - measures similarity/projection
- **Cosine similarity:** `cos(θ) = (a·b) / (||a|| ||b||)` - used in embeddings!
- **Matrix multiplication:** Composition of transformations

**Analogy:** Vectors are like arrows in space. Matrix multiplication is like applying a sequence of rotations, scaling, and shearing to those arrows.

**Key Insight for Embeddings:**
When you compute cosine similarity between two embedding vectors, you're literally measuring the angle between them in high-dimensional space. Similar meanings = small angle = high cosine similarity.

**What to practice:**
- Vector/matrix operations by hand (small examples)
- Understand dimensionality: 3D vectors you can visualize, 1536D embeddings you can't, but math is identical
- NumPy practice: This is how you'll actually implement it

---

### 1.2 Calculus (How Learning Happens)

**Why it matters:** Optimization = finding minimum of loss function = calculus.

#### Derivatives

**Single variable:**
- `f'(x)` = rate of change of `f` at point `x`
- Positive derivative = function increasing
- Zero derivative = local min/max

**Partial derivatives:**
- Function of many variables: `f(x₁, x₂, ..., xₙ)`
- `∂f/∂xᵢ` = rate of change in direction of `xᵢ` only

**Gradient:**
- Vector of all partial derivatives: `∇f = [∂f/∂x₁, ∂f/∂x₂, ..., ∂f/∂xₙ]`
- **Crucially:** Points in direction of steepest ascent
- **Gradient descent:** Go opposite direction to minimize

**Analogy:** Imagine you're blindfolded on a mountain (loss landscape) trying to reach the valley (minimum loss). The gradient tells you which direction is downhill. Take small steps opposite to gradient → reach bottom.

**Chain Rule (Most Important for Neural Networks):**
```
If y = f(g(x)), then dy/dx = (df/dg) × (dg/dx)
```

**Why critical:** Neural networks are compositions of functions. Backpropagation = chain rule applied repeatedly.

**Concrete Example:**
```
Loss = (prediction - truth)²
prediction = w₁x + w₀
∂Loss/∂w₁ = 2(prediction - truth) × x  [chain rule!]
```

---

### 1.3 Probability & Statistics (Dealing with Uncertainty)

**Why it matters:** Data is noisy, predictions are probabilistic, need to quantify uncertainty.

#### Core Concepts

**Probability Distribution:**
- Describes how likely different outcomes are
- Example: "This email is 92% likely spam"

**Expected Value:**
- Average outcome if you repeat experiment many times
- `E[X] = Σ x × P(x)`

**Variance:**
- How spread out values are
- Low variance = consistent, high variance = unpredictable

**Bayes' Theorem:**
```
P(A|B) = P(B|A) × P(A) / P(B)
```
- Posterior = Likelihood × Prior / Evidence
- **Analogy:** Medical test. P(Disease|Positive Test) depends on how accurate test is AND how rare disease is.

**In ML Context:**
- Training = learning probability distributions from data
- Inference = computing probabilities of outcomes
- Bayesian approaches explicitly model uncertainty

---

## Part 2: Machine Learning Fundamentals (Week 2)

### 2.1 The ML Pipeline

**The Core Loop:**
```
1. Data → Model → Predictions
2. Compare predictions to truth (loss function)
3. Adjust model to reduce loss (optimization)
4. Repeat
```

**Analogy:** Learning to throw darts.
- **Data:** Your previous throws and where they landed
- **Model:** Your mental model of "how hard to throw, what angle"
- **Loss:** Distance from bullseye
- **Optimization:** Adjusting your technique to get closer

---

### 2.2 Training vs Validation vs Test

**Training Set (70%):**
- Data used to fit model parameters
- Model sees this during learning

**Validation Set (15%):**
- Used to tune hyperparameters
- Check "how well are we learning?" during training
- Guide decisions like "should I train longer?"

**Test Set (15%):**
- **Never** used during development
- Final evaluation only
- Simulates "real world" performance

**Why split?**
- **Overfitting:** Model memorizes training data instead of learning patterns
- Like studying for exam by memorizing answers, then failing on new questions
- Validation/test sets catch this

**Analogy:** Training set = practice problems with answers. Validation set = practice exam. Test set = real final exam you can only take once.

---

### 2.3 Gradient Descent (How Models Learn)

**Goal:** Minimize loss function `L(θ)` where `θ` = model parameters

**Algorithm:**
```
1. Initialize θ randomly
2. Repeat:
   - Compute gradient: ∇L(θ)
   - Update: θ = θ - α × ∇L(θ)
   - (α = learning rate, how big steps to take)
3. Until convergence (gradient ≈ 0)
```

**Variants:**

**Batch Gradient Descent:**
- Compute gradient using ALL data points
- Accurate but slow for large datasets

**Stochastic Gradient Descent (SGD):**
- Compute gradient using ONE random data point
- Fast but noisy

**Mini-batch Gradient Descent:**
- Compromise: Use small batches (e.g., 32 examples)
- Best of both worlds - used in practice

**Learning Rate (α):**
- Too high: Overshoot minimum, diverge
- Too low: Take forever to converge
- Modern: Adaptive methods (Adam, RMSprop) adjust automatically

---

### 2.4 Overfitting and Generalization

**Overfitting:**
- Model too complex for data
- Fits training perfectly but fails on new data
- Like memorizing specific practice problems instead of understanding concepts

**Underfitting:**
- Model too simple
- Can't capture patterns even in training data
- Like trying to fit curved data with straight line

**Regularization (Fighting Overfitting):**

**L2 Regularization (Weight Decay):**
- Add penalty for large weights: `Loss = Original Loss + λΣwᵢ²`
- Forces model to use simpler explanations
- **Analogy:** Occam's Razor - prefer simpler models

**Dropout:**
- Randomly "turn off" neurons during training
- Forces network to be robust, not rely on specific paths
- **Analogy:** Training with handicaps makes you stronger

**Early Stopping:**
- Stop training when validation loss stops improving
- Don't overfit by training too long

**Data Augmentation:**
- Create more training data by modifying existing
- For code: variable renaming, reordering functions

---

## Part 3: Neural Networks (Week 3)

### 3.1 The Neuron (Building Block)

**Biological Inspiration (Loose):**
- Neuron receives signals → processes → fires if threshold exceeded

**Artificial Neuron:**
```
Input: x = [x₁, x₂, ..., xₙ]
Weights: w = [w₁, w₂, ..., wₙ]
Bias: b

1. Weighted sum: z = w₁x₁ + w₂x₂ + ... + wₙxₙ + b = w·x + b
2. Activation: a = σ(z)
3. Output: a
```

**Activation Functions (σ):**

**ReLU (Rectified Linear Unit):** `f(x) = max(0, x)`
- Most common in modern networks
- Simple, fast, avoids vanishing gradients
- "Turn off negative signals"

**Sigmoid:** `f(x) = 1/(1+e^(-x))`
- Outputs 0 to 1 (interpretable as probability)
- Used in output layers for binary classification
- Problem: Gradients vanish for large |x|

**Tanh:** `f(x) = (e^x - e^(-x))/(e^x + e^(-x))`
- Outputs -1 to 1
- Zero-centered (better than sigmoid)
- Still has vanishing gradient problem

**Why activation functions?**
Without them, stack of linear layers = one linear layer. Need nonlinearity to model complex patterns.

**Analogy:** Neurons are like decision makers. Weighted sum = "considering all inputs proportionally". Activation = "deciding whether to fire based on evidence".

---

### 3.2 Feedforward Networks

**Architecture:**
```
Input → Hidden Layer 1 → Hidden Layer 2 → ... → Output
```

**Each layer:**
- Matrix multiplication: `z = Wx + b`
- Activation: `a = σ(z)`
- Output becomes input to next layer

**Universal Approximation Theorem:**
A neural network with sufficient hidden units can approximate *any* continuous function.

**Depth vs Width:**
- **Wide networks:** Many neurons per layer (capacity)
- **Deep networks:** Many layers (hierarchical features)
- Modern trend: Deeper is better (with residual connections)

---

### 3.3 Backpropagation (How Networks Learn)

**The Problem:**
We know ∂Loss/∂output, but need ∂Loss/∂weights in every layer.

**Solution: Chain Rule Backwards:**
```
Output layer → Hidden layer 2 → Hidden layer 1 → Input
Compute gradients in reverse order
```

**Algorithm (Simplified):**
```
Forward pass: Compute predictions
Compute loss
Backward pass:
  For each layer (starting from output):
    1. Compute gradient of loss w.r.t. layer output
    2. Compute gradient w.r.t. weights (∂L/∂W)
    3. Compute gradient w.r.t. inputs (pass to previous layer)
Update weights: W = W - α × ∂L/∂W
```

**Why it works:**
Chain rule + careful bookkeeping. Each layer computes its gradient and passes relevant info backward.

**Vanishing Gradients Problem:**
- Deep networks: Gradients get multiplied many times
- If < 1, they shrink to ~0 (vanish)
- Early layers barely learn

**Solutions:**
- ReLU activations (don't saturate)
- Batch normalization
- Residual connections (skip connections)

---

## Part 4: Modern Architectures (Week 4)

### 4.1 Attention Mechanism (Revolutionary)

**Problem with RNNs/LSTMs:**
- Process sequences one token at a time
- Information bottleneck: Later tokens don't "see" early tokens clearly
- Long sequences = information loss

**Attention: "Look at everything relevant"**

**Key Idea:**
For each token, compute how relevant every other token is, then combine information proportionally.

**Mechanism:**
```
1. Query (Q): "What am I looking for?"
2. Key (K): "What information do I have?"
3. Value (V): "What information to return?"

Attention(Q, K, V) = softmax(Q·K^T / √d) × V
```

**Step by step:**
1. Q·K^T = Similarity scores between query and all keys
2. Divide by √d = Scaling (prevents huge numbers)
3. Softmax = Convert to probabilities (weights sum to 1)
4. Multiply by V = Weighted sum of values

**Analogy:** Library search.
- Query = Your question
- Keys = Book titles/topics
- Values = Book contents
- Attention = Finding relevant books, reading them proportionally to relevance

**Why revolutionary:**
- Parallel processing (no sequential bottleneck)
- Direct connections between any tokens
- Foundation of transformers

---

### 4.2 Transformers (The Architecture That Changed Everything)

**Architecture Overview:**
```
Input Tokens → Embeddings → 
  ↓
Encoder Stack (N layers):
  - Multi-head Self-Attention
  - Feed-forward Network
  ↓
Decoder Stack (N layers):
  - Masked Self-Attention
  - Cross-Attention (to encoder)
  - Feed-forward Network
  ↓
Output Tokens
```

**Key Components:**

**Multi-Head Attention:**
- Run attention multiple times in parallel (8-16 "heads")
- Each head learns different relationships
- Example: One head = syntax, another = semantics, another = coreference

**Self-Attention:**
- Token attends to *all* tokens in sequence (including itself)
- Builds contextual representations
- "function" token looks at "def", "arguments", "body" → understands it's a function definition

**Positional Encoding:**
- Problem: Attention has no sense of order
- Solution: Add position information to embeddings
- Methods: Sinusoidal, learned embeddings

**Layer Normalization:**
- Stabilizes training
- Normalizes activations to have mean 0, variance 1

**Residual Connections:**
- `Output = Layer(Input) + Input`
- Allows gradients to flow backward easily
- Enables training very deep networks (100+ layers)

**Why transformers dominate:**
- Parallelizable (fast training)
- Scale beautifully (bigger = better)
- State-of-the-art across NLP, vision, code

---

### 4.3 BERT, GPT, and Modern LLMs

**BERT (Bidirectional Encoder Representations from Transformers):**
- Encoder-only architecture
- Pre-training: Masked Language Modeling (predict masked words)
- Bidirectional context (sees both left and right)
- Great for understanding tasks: classification, Q&A, NER

**GPT (Generative Pre-trained Transformer):**
- Decoder-only architecture
- Pre-training: Causal Language Modeling (predict next token)
- Unidirectional (only sees left context)
- Great for generation: text completion, dialogue

**Modern LLMs (GPT-4, Claude):**
- Massive scale: Billions of parameters
- Trained on trillions of tokens
- Emergent abilities: Few-shot learning, reasoning, coding
- Architecture details often proprietary, but transformer-based

**Training Process:**
1. **Pre-training:** Self-supervised on massive text corpus
2. **Fine-tuning:** Supervised on specific tasks (optional)
3. **RLHF (Reinforcement Learning from Human Feedback):** Align with human preferences

---

## Part 5: Embeddings Deep Dive (Week 5)

### 5.1 Word Embeddings

**Goal:** Represent words as vectors that capture meaning.

**Word2Vec (2013):**
- Two approaches: CBOW (predict word from context), Skip-gram (predict context from word)
- Training: Shallow neural network on large corpus
- Result: Semantic relationships in vector space
- Famous: `king - man + woman ≈ queen`

**GloVe (Global Vectors):**
- Matrix factorization on word co-occurrence statistics
- Captures both local and global context
- Similar quality to Word2Vec, different approach

**Limitations:**
- One embedding per word (no context)
- "bank" (financial) and "bank" (river) = same embedding

---

### 5.2 Contextual Embeddings

**ELMo (2018):**
- Bidirectional LSTM
- Different embedding for same word in different contexts
- "bank" in "bank account" vs "river bank" = different vectors

**BERT Embeddings:**
- Token embeddings from BERT model
- Full bidirectional context
- State-of-art for understanding

**Sentence Transformers:**
- BERT fine-tuned for sentence-level embeddings
- Used in semantic search, RAG systems
- Models: `all-MiniLM-L6-v2`, `all-mpnet-base-v2`

---

### 5.3 Code Embeddings

**Challenges:**
- Code has syntax and semantics
- Names matter less than structure
- Need to capture program behavior

**CodeBERT:**
- BERT pre-trained on code
- Trained on code-comment pairs
- Understands code semantics

**GraphCodeBERT:**
- Incorporates code structure (AST, data flow)
- Better than token-only approaches

**OpenAI Codex Embeddings:**
- From model behind GitHub Copilot
- Strong code understanding
- Proprietary

**For RAG:**
- `text-embedding-3-small/large` work well for code
- Specialized models slightly better but harder to use
- Tradeoff: Convenience vs marginal quality gain

---

### 5.4 How to Use Embeddings in RAG

**Embedding Strategy:**

**Option 1: Chunk-level only**
- Embed each code chunk independently
- Fast, simple
- May miss cross-file relationships

**Option 2: Hierarchical**
- File-level embeddings (summary)
- Chunk-level embeddings (details)
- Two-stage retrieval: Find relevant files → find relevant chunks

**Option 3: With metadata**
- Embed: `[metadata] + code + [comments/docstrings]`
- Richer context in embedding
- Better retrieval

**Similarity Metrics:**

**Cosine Similarity (Most Common):**
```
cos(a, b) = (a·b) / (||a|| ||b||)
```
- Range: [-1, 1] (in practice, [0, 1] for embeddings)
- Ignores magnitude, only direction

**Euclidean Distance:**
```
d(a, b) = ||a - b|| = √(Σ(aᵢ-bᵢ)²)
```
- Considers magnitude
- Less common for high-dimensional embeddings

**Dot Product:**
- `a·b = Σaᵢbᵢ`
- Fast but magnitude-dependent
- Used when embeddings are normalized

---

## Part 6: Advanced RAG Concepts (Week 6)

### 6.1 Retrieval Strategies

**Naive RAG:**
```
Query → Embed → Vector search → Top K → LLM
```

**Problems:**
- May retrieve irrelevant chunks
- No ranking by query-specific relevance
- Ignores document structure

**Improved: Hybrid Search**
```
1. Semantic search (embeddings)
2. Keyword search (BM25, TF-IDF)
3. Combine scores (weighted average or reciprocal rank fusion)
```

**Why better:** Catches both semantic similarity and exact keyword matches.

**Advanced: HyDE (Hypothetical Document Embeddings)**
```
1. Query: "How do we handle errors?"
2. LLM generates hypothetical code that answers
3. Embed hypothetical code
4. Search for similar real code
```

**Why works:** Hypothetical answer is closer to actual code than question is.

---

### 6.2 Reranking

**Problem:** Initial retrieval (top 20) may have false positives.

**Solution: Two-stage retrieval**
```
1. Fast retrieval: Get top 20-50 candidates (embedding search)
2. Slow reranking: Use more expensive model to rerank top candidates
```

**Reranking Models:**
- Cross-encoders (BERT-based)
- Pass (query, document) pair → relevance score
- More accurate but slower (can't pre-compute)

**Implementation:**
```python
# Stage 1: Fast retrieval
candidates = vector_db.search(query, k=20)

# Stage 2: Rerank
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
scores = reranker.predict([(query, c.text) for c in candidates])
top_k = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)[:5]
```

---

### 6.3 Query Transformation

**Problem:** User query may not be optimal for retrieval.

**Techniques:**

**Query Expansion:**
- Add synonyms, related terms
- "authentication" → "authentication, login, auth, JWT, session"

**Query Decomposition:**
- Complex query → multiple simple queries
- "How do we handle auth and logging?" → Two queries, combine results

**Step-back Prompting:**
- Ask more general question first
- "Show rate limiting in API" → First: "What is our API structure?"
- Provides broader context

---

### 6.4 Graph-Enhanced RAG

**Problem:** Code has relationships (imports, calls, inheritance).

**Solution: Graph database + vector database**

**Architecture:**
```
Vector DB: Semantic search
Graph DB: Relationship traversal

Combined:
1. Vector search finds relevant starting nodes
2. Graph traversal finds connected code
3. Both contexts → LLM
```

**Example:**
Query: "How does authentication flow work?"
1. Vector search finds `authenticateUser()` function
2. Graph traversal:
   - Find callers of this function
   - Find functions it calls
   - Find related config files
3. Return entire authentication pipeline

**Implementations:**
- Neo4j + vector index
- Weaviate (built-in graph features)
- Custom: NetworkX + Chroma

---

### 6.5 Fine-tuning Embeddings

**When to fine-tune:**
- Domain-specific vocabulary (your org's terminology)
- Poor retrieval quality with off-the-shelf models
- Have labeled data (query, relevant documents)

**Approaches:**

**Contrastive Learning:**
- Training data: (query, positive doc, negative doc) triples
- Loss: Push query closer to positive, away from negative
- Used by Sentence Transformers

**Hard Negative Mining:**
- Negative examples that are semantically close but wrong
- Forces model to learn subtle distinctions

**Implementation:**
```python
from sentence_transformers import SentenceTransformer, losses

model = SentenceTransformer('all-MiniLM-L6-v2')

train_examples = [
    InputExample(texts=['query', 'positive_doc', 'negative_doc']),
    # ... more examples
]

train_loss = losses.TripletLoss(model)
model.fit(train_objectives=[(train_dataloader, train_loss)])
```

---

## Part 7: Production Considerations

### 7.1 Scaling to N Repos

**Challenges:**
- Millions of files
- Embedding API costs
- Index size and query speed
- Updates and versioning

**Architecture for Scale:**

**Incremental Indexing:**
- Don't re-embed everything on each update
- Track file hashes, re-embed only changed files
- Metadata: last_updated, version

**Distributed Vector DB:**
- Pinecone, Weaviate, Milvus (handle millions of vectors)
- Sharding, replication
- Managed service vs self-hosted

**Cost Optimization:**
- Batch embedding API calls (reduce overhead)
- Cache embeddings
- Consider open-source models (inference on your hardware)

**Update Strategy:**
```
1. Git webhook → code changed
2. Identify changed files (git diff)
3. Re-chunk and re-embed changed files
4. Update vector DB (upsert)
5. Prune deleted files
```

---

### 7.2 Evaluation and Monitoring

**Offline Metrics:**
- Recall@K, Precision@K
- Mean Reciprocal Rank (MRR)
- NDCG (Normalized Discounted Cumulative Gain)

**Online Metrics:**
- User feedback (thumbs up/down)
- Query latency
- Cache hit rate
- LLM token usage (cost)

**A/B Testing:**
- Control: Current system
- Treatment: New retrieval strategy
- Metric: User satisfaction, task completion

**Logging:**
```python
{
  "query": "...",
  "retrieved_chunks": [...],
  "relevance_scores": [...],
  "user_feedback": "positive/negative",
  "latency_ms": 234,
  "timestamp": "..."
}
```

---

### 7.3 Security and Privacy

**Concerns:**
- Code may contain secrets (API keys, passwords)
- Access control (who can query which repos)
- Embeddings leak information (can reconstruct text)

**Mitigations:**
- Secret scanning before embedding
- Metadata-based access control
- Audit logs
- On-premise deployment for sensitive code

---

## Part 8: Beyond RAG - Future Directions

### 8.1 Agentic RAG

**Concept:** LLM decides when/how to retrieve

**Example:**
```
User: "Refactor authentication to use OAuth2"

Agent:
1. Retrieves current auth code
2. Retrieves OAuth2 library docs
3. Plans refactoring steps
4. Retrieves specific implementation patterns
5. Generates refactored code
```

**Frameworks:** LangChain Agents, AutoGPT, BabyAGI

---

### 8.2 Long-Context Models

**Trend:** Context windows growing (Claude: 200K, Gemini: 1M tokens)

**Implications for RAG:**
- Could embed entire small codebases in context
- RAG still needed for: Cost, speed, precision
- Hybrid: RAG for discovery, long-context for deep analysis

---

### 8.3 Multimodal RAG

**Beyond text:**
- Diagrams (architecture, flowcharts)
- Screenshots (UI code)
- Video (code walkthroughs)

**Unified embedding space:**
- CLIP-like models for code + diagrams
- Retrieve across modalities

---

## Appendix: Math Refresher Exercises

### Linear Algebra
1. Compute dot product of `[1, 2, 3]` and `[4, 5, 6]`
2. Compute cosine similarity between `[1, 0]` and `[1, 1]`
3. Multiply matrices: `[[1, 2], [3, 4]]` × `[[5, 6], [7, 8]]`

### Calculus
1. Compute derivative of `f(x) = 3x² + 2x + 1`
2. Compute gradient of `f(x, y) = x² + 2xy + y²`
3. Apply chain rule: `f(g(x))` where `f(u) = u²`, `g(x) = 3x + 1`

### Probability
1. Compute expected value of dice roll
2. Apply Bayes' theorem: Disease test problem
3. Compute variance of `[1, 2, 3, 4, 5]`

---

## Learning Resources

**Books:**
- "Deep Learning" by Goodfellow, Bengio, Courville (comprehensive)
- "Dive into Deep Learning" (interactive, free online)
- "Speech and Language Processing" by Jurafsky & Martin (NLP)

**Courses:**
- Stanford CS224N (NLP)
- Fast.ai (practical deep learning)
- DeepLearning.AI specialization

**Papers to Read:**
- "Attention Is All You Need" (Transformers)
- "BERT: Pre-training of Deep Bidirectional Transformers"
- "Dense Passage Retrieval for Open-Domain Question Answering" (RAG foundations)

**Hands-on:**
- Kaggle competitions
- Reproduce paper results
- Build projects (like this RAG system!)

---

## What's Not Covered (But Worth Exploring Later)

- Reinforcement Learning
- GANs (Generative Adversarial Networks)
- Diffusion Models
- Graph Neural Networks (beyond basics)
- Model compression (quantization, pruning, distillation)
- Federated Learning
- Multi-task Learning
- Meta-learning

---

**This document is your foundation. Refer back as you build and encounter concepts. Theory enables deeper practice; practice validates theory.**