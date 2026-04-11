# ml/anomaly/deep_learning.py
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


torch.manual_seed(42)
np.random.seed(42)


class LSTMAutoencoder(nn.Module):
    def __init__(self, seq_len, n_features, embedding_dim=16):
        super().__init__()
        self.encoder = nn.LSTM(input_size=n_features, hidden_size=embedding_dim,
                               num_layers=1, batch_first=True)
        self.decoder = nn.LSTM(input_size=embedding_dim, hidden_size=n_features,
                               num_layers=1, batch_first=True)

    def forward(self, x):
        encoded, (hidden, _) = self.encoder(x)
        hidden_repeated = hidden[-1].unsqueeze(1).repeat(1, x.shape[1], 1)
        decoded, _ = self.decoder(hidden_repeated)
        return decoded

def create_sequences(values, seq_len=7):
    sequences = []
    for i in range(len(values) - seq_len + 1):
        sequences.append(values[i:i + seq_len])
    return np.array(sequences)

def train_lstm_autoencoder(features_df, cost_col='total_cost', seq_len=7, epochs=30):
    """Trains LSTM Autoencoder and returns anomaly flags + reconstruction error"""
    data = features_df[[cost_col]].fillna(0).values
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)

    if len(data_scaled) <= seq_len:
        return pd.DataFrame({
            'is_anomaly_lstm': [0] * len(features_df),
            'lstm_reconstruction_error': [0.0] * len(features_df)
        }, index=features_df.index)

    sequences = create_sequences(data_scaled, seq_len)
    X_tensor = torch.FloatTensor(sequences)

    model = LSTMAutoencoder(seq_len=seq_len, n_features=1)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        predictions = model(X_tensor)
        loss = criterion(predictions, X_tensor)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        predictions = model(X_tensor)
        mse_per_sequence = torch.mean((predictions - X_tensor) ** 2, dim=[1, 2]).numpy()

    threshold = np.percentile(mse_per_sequence, 95)

    anomaly_flags = [0] * (seq_len - 1)
    for mse in mse_per_sequence:
        anomaly_flags.append(1 if mse > threshold else 0)

    reconstruction_error = [0.0] * (seq_len - 1) + list(mse_per_sequence)

    return pd.DataFrame({
        'is_anomaly_lstm': anomaly_flags,
        'lstm_reconstruction_error': reconstruction_error
    }, index=features_df.index)