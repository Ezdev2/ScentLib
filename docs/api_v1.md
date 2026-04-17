# ScentLib API - Documentation du Pilote (v1.0)

L'API ScentLib transforme le SDK en un service réseau. Elle permet l'interopérabilité entre le moteur de calcul (Python) et les interfaces (Web, Mobile) ou les entrées (Capteurs).

## Démarrage du Service
Pour activer le "Pilote", utilisez la commande :
`scentlib serve [--port PORT]`

Défaut : `http://127.0.0.1:8000`

---

## Points d'entrée (Endpoints)

### 1. Système
* **`GET /`** : Vérifie si le driver est en ligne.
* **`GET /docs`** : Accède à l'interface Swagger interactive pour tester les routes.

### 2. Bibliothèque de Molécules
* **`GET /scents`**
    * **Description** : Liste tous les identifiants disponibles dans la base.
    * **Réponse** : `{"count": 50, "scents": ["cid_1183", "cid_10430", ... ]}`

* **`GET /scents/{id}`**
    * **Description** : Récupère l'objet `.scent` complet.
    * **Utilité** : Fournit les données vectorielles pour dessiner le **Radar Chart**.
    * **Données incluses** : Labels, chimie (SMILES), intensités et Fingerprint.

### 3. Intelligence Visuelle (Prédiction)
* **`GET /scents/{id}/color`**
    * **Description** : Calcule la signature chromatique d'une odeur.
    * **Logique** : Analyse les groupements chimiques pour renvoyer une couleur hexadécimale.

---

## Intégration Frontend (Exemple JavaScript)

Pour ton futur Scent Player en Vue.js, voici comment tu récupéreras une odeur :

```javascript
const response = await fetch('[http://127.0.0.1:8000/scents/cid_1183](http://127.0.0.1:8000/scents/cid_1183)');
const scentData = await response.json();

console.log("Nom:", scentData.labels.layer3_descriptor);
console.log("Données pour le Chart:", scentData.data);